import logging
from typing import Any, Dict, Union, cast

import numpy as np
from rest_framework import serializers
from sklearn.preprocessing import MultiLabelBinarizer  # type: ignore

from apps.games.models import Game
from apps.recommendation.constants.today_constants import QUESTIONS_DATA
from apps.recommendation.utils.redis_utils import (
    find_similar_games,
    get_all_categories,
    get_all_genres,
    get_numerical_bounds,
    get_vector_redis_connection,
)

logger = logging.getLogger(__name__)


# min/max 값을 가진 구조의 틀
class RangeSerializer(serializers.Serializer[Any]):
    min = serializers.FloatField()
    max = serializers.FloatField()


class GameQuestionStepSerializer(serializers.Serializer[Any]):
    step = serializers.IntegerField()

    def validate_step(self, value: int) -> int:

        if value not in QUESTIONS_DATA:
            raise serializers.ValidationError("유효하지 않은 질문 단계입니다. 1에서 5 사이의 값만 사용할 수 있습니다.")
        return value


class TodayRecommendedGameSerializer(serializers.ModelSerializer[Game]):
    category = serializers.SerializerMethodField()
    players = serializers.SerializerMethodField()
    difficulty = serializers.SerializerMethodField()
    top_review = serializers.SerializerMethodField()

    class Meta:
        model = Game
        fields = [
            "title",
            "thumbnail_url",
            "category",
            "players",
            "difficulty",
            "top_review",
            "description",
        ]

    def get_category(self, obj: Game) -> str | None:
        first_category = obj.categories.first()
        return first_category.name if first_category else None

    def get_players(self, obj: Game) -> str:
        if obj.min_players == obj.max_players:
            return f"{obj.min_players}인"
        return f"{obj.min_players}-{obj.max_players}인"

    def get_difficulty(self, obj: Game) -> str:
        if obj.difficulty < 2.0:
            return "쉬움"
        elif obj.difficulty < 4.0:
            return "중급"
        else:
            return "어려움"

    def get_top_review(self, obj: Game) -> Union[Dict[str, str], None]:
        top_review_obj = obj.reviewed_by_users.select_related("user").filter(rating__gt=3).order_by("-rating").first()

        if top_review_obj and top_review_obj.content:
            return {"nickname": top_review_obj.user.nickname, "content": top_review_obj.content}

        return None


class TodayRecommendationResponseSerializer(serializers.Serializer[Any]):
    message = serializers.CharField()
    games = serializers.ListField(child=TodayRecommendedGameSerializer())


class TodayGameRequestSerializer(serializers.Serializer[Any]):
    categories = serializers.ListField(child=serializers.CharField(), required=True)
    players_range = RangeSerializer(required=True)
    playtime_range = RangeSerializer(required=True)
    age_group = RangeSerializer(required=True)
    difficulty_range = RangeSerializer(required=True)

    def validate_categories(self, value: list[str]) -> list[str]:
        all_categories = get_all_categories()
        invalid_categories = [cat for cat in value if cat not in all_categories and cat != "상관없음"]
        if invalid_categories:
            raise serializers.ValidationError(
                f"존재하지 않는 카테고리가 포함되어 있습니다: {', '.join(invalid_categories)}"
            )
        return value

    def _normalize_value(self, value: float, feature: str) -> float:
        bounds = get_numerical_bounds()
        min_val, max_val = bounds.get(feature, (0, 1))
        if (max_val - min_val) == 0:
            return 0.5
        scaled = (value - min_val) / (max_val - min_val)
        return float(np.clip(scaled, 0.0, 1.0))

    def _create_query_vector(self) -> np.ndarray:
        data = self.validated_data
        all_genres, all_categories = get_all_genres(), get_all_categories()
        genre_vector = np.zeros(len(all_genres), dtype=np.float32)
        if "상관없음" in data["categories"] or not data["categories"]:
            category_vector = np.zeros(len(all_categories), dtype=np.float32)
        else:
            category_binarizer = MultiLabelBinarizer(classes=all_categories)
            category_vector = category_binarizer.fit_transform([data["categories"]])[0]

        age = (data["age_group"]["min"] + data["age_group"]["max"]) / 2
        players_min = data["players_range"]["min"]
        players_max = data["players_range"]["max"]
        playtime_min = data["playtime_range"]["min"]
        playtime_max = data["playtime_range"]["max"]
        difficulty = (data["difficulty_range"]["min"] + data["difficulty_range"]["max"]) / 2

        numerical_vector = np.array(
            [
                self._normalize_value(age, "age"),
                self._normalize_value(players_min, "players"),
                self._normalize_value(players_max, "players"),
                self._normalize_value(playtime_min, "playtime"),
                self._normalize_value(playtime_max, "playtime"),
                self._normalize_value(difficulty, "difficulty"),
            ]
        )

        logger.info("사용자 설문 답변 기반의 쿼리 벡터를 성공적으로 생성했습니다.")
        return cast(np.ndarray, np.concatenate([genre_vector, category_vector, numerical_vector]).astype(np.float32))

    def _get_recommendations(self) -> list[Game]:
        redis_conn = get_vector_redis_connection()
        if redis_conn is None:
            raise serializers.ValidationError({"detail": "추천 시스템에 연결할 수 없습니다."})
        query_vector = self._create_query_vector()
        similar_game_ids = find_similar_games(redis_conn=redis_conn, user_vector=query_vector, exclude_ids=set(), k=10)
        games_map = {game.game_id: game for game in Game.objects.filter(game_id__in=similar_game_ids)}
        recommended_games = [games_map[game_id] for game_id in similar_game_ids if game_id in games_map]
        if len(recommended_games) < 10:
            num_needed = 10 - len(recommended_games)
            fallback_games = list(
                Game.objects.exclude(game_id__in=set(similar_game_ids)).order_by("-like_count", "-average_rating")[
                    :num_needed
                ]
            )
            recommended_games.extend(fallback_games)
        return recommended_games

    def get_response(self) -> dict[str, Any]:
        recommendations = self._get_recommendations()
        message = "오늘의 추천 게임 목록을 성공적으로 불러왔습니다."
        if not recommendations:
            message = "조건에 맞는 추천 게임을 찾지 못했습니다."
        response_data = {"message": message, "games": recommendations}
        response_serializer = TodayRecommendationResponseSerializer(response_data, context=self.context)
        return response_serializer.data
