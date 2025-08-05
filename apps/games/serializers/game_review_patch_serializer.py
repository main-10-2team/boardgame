from rest_framework import serializers

from apps.games.models import Review


class GameReviewPatchRequestSerializer(serializers.ModelSerializer[Review]):
    rating = serializers.FloatField(
        required=False,
        min_value=0.0,
        max_value=5.0,
    )
    content = serializers.CharField(required=False, max_length=500, allow_blank=True, trim_whitespace=True)

    class Meta:
        model = Review
        fields = ["rating", "content"]

    def validate_rating(self, value: float) -> float:
        if value * 2 != int(value * 2):
            raise serializers.ValidationError("유효하지 않은 평점입니다.")
        return value

    def validate_content(self, value: str) -> str:
        if not value.strip():
            raise serializers.ValidationError("리뷰 내용 입력해주세요.")
        return value


class ReviewPatchResponseReviewSerializer(serializers.ModelSerializer[Review]):
    nickname = serializers.SerializerMethodField()
    game_id = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = [
            "review_id",
            "game_id",
            "user_id",
            "nickname",
            "rating",
            "content",
            "created_at",
            "updated_at",
        ]

    def get_nickname(self, obj: Review) -> str:
        return obj.user.nickname

    def get_game_id(self, obj: Review) -> int:
        return obj.game.game_id
