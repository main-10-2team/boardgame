from rest_framework import serializers

from apps.games.models import Review


class ReviewListSerializer(serializers.ModelSerializer[Review]):
    nickname = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = [
            "review_id",
            "nickname",
            "rating",
            "content",
            "created_at",
        ]

    def get_nickname(self, obj: Review) -> str:
        return obj.user.nickname
