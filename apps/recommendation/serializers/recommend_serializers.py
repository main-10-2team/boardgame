import logging
from collections import Counter
from typing import Any, Counter as TypingCounter

import numpy as np
from django.db.models import Exists, OuterRef, QuerySet
from redis import Redis
from rest_framework import serializers

from apps.games.models import Game, GameViewLog, Like, Review
from apps.recommendation.utils.redis_utils import (
    find_similar_games,
    get_vector_redis_connection,
)

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
        return getattr(obj, "is_liked", False)


class RecommendationResponseSerializer(serializers.Serializer[Any]):
    message = serializers.CharField()
    data = RecommendedGameSerializer(many=True)  # type: ignore


class RecommendationSerializer(serializers.Serializer[Any]):

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        self.recommended_games: list[Game] = []
        self.positive_interaction_game_ids: set[int] = set()

    def _get_positive_interaction_game_ids_queryset(self) -> QuerySet[Any]:
        liked_games_qs = Like.objects.filter(user=self.user).values_list("game_id", flat=True)
        high_rated_games_qs = Review.objects.filter(user=self.user, rating__gte=3.5).values_list("game_id", flat=True)
        viewed_games_qs = GameViewLog.objects.filter(user=self.user).values_list("game_id", flat=True)

        combined_ids_qs = liked_games_qs.union(high_rated_games_qs, viewed_games_qs)
        return combined_ids_qs

    def get_recommendations(self) -> list[Any]:
        if not self.user or not self.user.is_authenticated:
            raise serializers.ValidationError({"detail": "인증되지 않은 사용자입니다."})

        r = get_vector_redis_connection()
        if r is None:
            raise serializers.ValidationError({"detail": "Redis 서버에 연결할 수 없습니다. 잠시 후 다시 시도해주세요."})

        seed_game_vectors = self._get_positive_interaction_games(r)

        if not seed_game_vectors:
            logger.info(f"사용자 ID {self.user.user_id}의 활동 기록이 없어, 대체 추천을 제공합니다.")
            self.recommended_games = self._get_fallback_recommendations()
        else:
            logger.info(
                f"사용자 ID {self.user.user_id}의 씨앗 게임 {len(seed_game_vectors)}개를 기반으로 추천을 생성합니다."
            )
            self.recommended_games = self._get_seed_based_recommendations(r, seed_game_vectors)

        return self.recommended_games

    def _get_positive_interaction_games(self, redis_conn: Redis) -> list[np.ndarray]:
        self.positive_interaction_game_ids = set(self._get_positive_interaction_game_ids_queryset())

        if not self.positive_interaction_game_ids:
            return []

        game_vectors = []
        pipeline = redis_conn.pipeline(transaction=False)
        for game_id in self.positive_interaction_game_ids:
            pipeline.hget(f"game:{game_id}", "vector_full")
        results = pipeline.execute()
        for vec_bytes in results:
            if isinstance(vec_bytes, bytes):
                game_vectors.append(np.frombuffer(vec_bytes, dtype=np.float32))

        if not game_vectors:
            logger.warning(f"사용자 ID {self.user.user_id}의 게임에 대한 벡터 데이터를 찾을 수 없습니다.")
            return []

        return game_vectors

    def _get_fallback_recommendations(self) -> list[Any]:
        if not self.positive_interaction_game_ids:
            self.positive_interaction_game_ids = set(self._get_positive_interaction_game_ids_queryset())

        user_likes = Like.objects.filter(user=self.user, game=OuterRef("pk"))
        fallback_games = (
            Game.objects.exclude(game_id__in=self.positive_interaction_game_ids)
            .annotate(is_liked=Exists(user_likes))
            .prefetch_related("genres", "categories")
            .order_by("-like_count", "-average_rating")[:10]
        )

        if not fallback_games.exists():
            fallback_games = (
                Game.objects.exclude(game_id__in=self.positive_interaction_game_ids)
                .annotate(is_liked=Exists(user_likes))
                .prefetch_related("genres", "categories")
                .order_by("-created_at")[:10]
            )
        return list(fallback_games)

    def _get_seed_based_recommendations(
        self, redis_conn: Redis, seed_vectors: list[np.ndarray], k: int = 10
    ) -> list[Any]:
        recommendation_candidates: TypingCounter[int] = Counter()

        k_per_seed = 7

        for seed_vector in seed_vectors:
            similar_game_ids = find_similar_games(
                redis_conn=redis_conn,
                user_vector=seed_vector,
                exclude_ids=self.positive_interaction_game_ids,
                k=k_per_seed,
                index_name="game_index_full",
                vector_field_name="vector_full",
            )

            recommendation_candidates.update(similar_game_ids)

        for game_id in self.positive_interaction_game_ids:
            recommendation_candidates.pop(game_id, None)

        top_k_game_ids = [game_id for game_id, count in recommendation_candidates.most_common(k)]

        user_likes = Like.objects.filter(user=self.user, game=OuterRef("pk"))
        games_queryset = (
            Game.objects.filter(game_id__in=top_k_game_ids)
            .annotate(is_liked=Exists(user_likes))
            .prefetch_related("genres", "categories")
        )
        games_map = {game.game_id: game for game in games_queryset}
        recommended_games = [games_map[game_id] for game_id in top_k_game_ids if game_id in games_map]

        if len(recommended_games) < k:
            num_needed = k - len(recommended_games)
            exclude_ids = self.positive_interaction_game_ids.union(top_k_game_ids)

            fallback_games = list(
                Game.objects.exclude(game_id__in=exclude_ids)
                .annotate(is_liked=Exists(user_likes))
                .prefetch_related("genres", "categories")
                .order_by("-like_count", "-average_rating")[:num_needed]
            )
            recommended_games.extend(fallback_games)

        return recommended_games
