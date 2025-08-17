import logging
from typing import Any, cast

import numpy as np
from redis import Redis
from rest_framework import serializers

from apps.games.models import Game, GameViewLog, Like, Review
from apps.recommendation.utils.redis_utils import  find_similar_games, get_vector_redis_connection

logger = logging.getLogger(__name__)


class RecommendedGameSerializer(serializers.ModelSerializer[Game]):
    genre = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()
    difficulty = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()

    class Meta:
        model = Game
        fields = [
            "game_id",
            "title",
            "thumbnail_url",
            "difficulty",
            "average_rating",
            "reviews_count",
            "like_count",
            "genre",
            "category",
            "is_liked",
        ]

    def get_genre(self, obj: Game) -> str | None:
        first_genre = obj.genres.first()
        return first_genre.name if first_genre else None

    def get_category(self, obj: Game) -> str | None:
        first_category = obj.categories.first()
        return first_category.name if first_category else None

    def get_difficulty(self, obj: Game) -> str:
        if obj.difficulty < 2.0:
            return "쉬움"
        elif obj.difficulty < 4.0:
            return "중급"
        else:
            return "어려움"

    def get_is_liked(self, obj: Game) -> bool:
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return Like.objects.filter(user=request.user, game=obj).exists()


class RecommendationResponseSerializer(serializers.Serializer[Any]):
    message = serializers.CharField()
    data = RecommendedGameSerializer(many=True)  # type: ignore


class RecommendationSerializer(serializers.Serializer[Any]):

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        self.recommended_games: list[Game] = []
        self.positive_interaction_game_ids: set[int] = set()

    def get_recommendations(self) -> list[Game]:
        if not self.user or not self.user.is_authenticated:
            raise serializers.ValidationError({"detail": "인증되지 않은 사용자입니다."})

        r = get_vector_redis_connection()
        if r is None:
            raise serializers.ValidationError({"detail": "Redis 서버에 연결할 수 없습니다. 잠시 후 다시 시도해주세요."})

        user_vector = self._get_user_vector(r)

        if user_vector is None:
            logger.info(f"사용자 ID {self.user.user_id}의 활동 기록이 없어, 대체 추천을 제공합니다.")
            self.recommended_games = self._get_fallback_recommendations()
        else:
            logger.info(f"사용자 ID {self.user.user_id}의 취향 벡터를 계산했습니다.")
            self.recommended_games = self._get_vector_recommendations(r, user_vector)

        return self.recommended_games

    def _get_user_vector(self, redis_conn: Redis) -> np.ndarray | None:
        liked_games = Like.objects.filter(user=self.user).values_list("game_id", flat=True)
        high_rated_games = Review.objects.filter(user=self.user, rating__gte=3.5).values_list("game_id", flat=True)
        viewed_games = GameViewLog.objects.filter(user=self.user).values_list("game_id", flat=True).distinct()
        self.positive_interaction_game_ids = set(liked_games) | set(high_rated_games) | set(viewed_games)

        if not self.positive_interaction_game_ids:
            return None

        game_vectors = []
        pipeline = redis_conn.pipeline(transaction=False)
        for game_id in self.positive_interaction_game_ids:
            pipeline.hget(f"game:{game_id}", "vector")

        results = pipeline.execute()
        for vec_bytes in results:
            if isinstance(vec_bytes, bytes):
                game_vectors.append(np.frombuffer(vec_bytes, dtype=np.float32))

        if not game_vectors:
            logger.warning(f"사용자 ID {self.user.user_id}의 게임에 대한 벡터 데이터를 찾을 수 없습니다.")
            return None

        return cast(np.ndarray, np.mean(game_vectors, axis=0))

    def _get_fallback_recommendations(self) -> list[Game]:
        fallback_games = Game.objects.order_by("-like_count", "-average_rating")[:10]
        if not fallback_games.exists():
            fallback_games = Game.objects.order_by("-created_at")[:10]
        return list(fallback_games)

    def _get_vector_recommendations(self, redis_conn: Redis, user_vector: np.ndarray, k: int = 10) -> list[Game]:

        similar_game_ids = find_similar_games(
            redis_conn=redis_conn,
            user_vector=user_vector,
            exclude_ids=self.positive_interaction_game_ids,
            k=k,
        )

        games_map = {game.game_id: game for game in Game.objects.filter(game_id__in=similar_game_ids)}
        recommended_games = [games_map[game_id] for game_id in similar_game_ids if game_id in games_map]

        if len(recommended_games) < k:
            num_needed = k - len(recommended_games)

            exclude_ids = self.positive_interaction_game_ids.union(similar_game_ids)

            fallback_games = list(
                Game.objects.exclude(game_id__in=exclude_ids).order_by("-like_count", "-average_rating")[:num_needed]
            )
            recommended_games.extend(fallback_games)

            if len(recommended_games) < k:
                current_ids = {game.game_id for game in recommended_games}
                final_exclude_ids = self.positive_interaction_game_ids.union(current_ids)
                final_num_needed = k - len(recommended_games)

                if final_num_needed > 0:
                    newest_games = list(
                        Game.objects.exclude(game_id__in=final_exclude_ids).order_by("-created_at")[:final_num_needed]
                    )
                    recommended_games.extend(newest_games)
        return recommended_games
