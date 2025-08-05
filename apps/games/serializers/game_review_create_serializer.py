from typing import Any

from rest_framework import serializers

from apps.games.models import Game, Review
from apps.users.models import User


class ReviewCreateSerializer(serializers.ModelSerializer[Review]):
    rating = serializers.FloatField(min_value=1.0, max_value=5.0)
    content = serializers.CharField(required=False, allow_blank=True, max_length=500)

    class Meta:
        model = Review
        fields = ["rating", "content"]

    def validate_rating(self, value: float) -> float:
        if (value * 10) % 5 != 0:
            raise serializers.ValidationError("평점은 0.5 단위여야 합니다.")
        return value

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        user: User = self.context["request"].user
        game_id = self.context.get("game_id")

        if not game_id:
            raise serializers.ValidationError("게임 ID가 누락되었습니다.")

        try:
            game = Game.objects.get(game_id=game_id)
        except Game.DoesNotExist:
            raise serializers.ValidationError("유효하지 않은 게임 ID입니다.")

        if Review.objects.filter(user=user, game=game).exists():
            raise serializers.ValidationError("이미 해당 게임에 대한 리뷰가 존재합니다.")

        self.context["game"] = game
        return data


class ReviewResponseSerializer(serializers.ModelSerializer[Review]):
    user_id = serializers.SerializerMethodField()
    nickname = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = [
            "review_id",
            "user_id",
            "nickname",
            "rating",
            "content",
            "created_at",
        ]

    def get_user_id(self, obj: Review) -> int:
        return obj.user.user_id

    def get_nickname(self, obj: Review) -> str:
        return obj.user.nickname
