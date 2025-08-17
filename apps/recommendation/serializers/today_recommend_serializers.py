from typing import Any

from rest_framework import serializers

from apps.games.models import Game
from apps.recommendation.constants.today_constants import QUESTIONS_DATA


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

    def get_top_review(self, obj: Game) -> str | None:
        top_review_obj = obj.reviewed_by_users.filter(rating__gt=3).order_by("-rating").first()
        return top_review_obj.content if top_review_obj and top_review_obj.content else None


class TodayRecommendationResponseSerializer(serializers.Serializer[Any]):
    message = serializers.CharField()
    games = serializers.ListField(child=TodayRecommendedGameSerializer())
