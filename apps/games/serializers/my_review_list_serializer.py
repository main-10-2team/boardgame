from typing import Any, Dict

from rest_framework import serializers

from apps.games.models import Review


class MyReviewListSerializer(serializers.ModelSerializer[Review]):
    game_id = serializers.IntegerField(source="game.game_id", read_only=True)
    title = serializers.CharField(source="game.title", read_only=True)
    rating = serializers.FloatField()
    content = serializers.CharField()
    image_url = serializers.CharField(source="game.thumbnail_url", read_only=True)
    created_at = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%SZ")
    updated_at = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%SZ")
    actions = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = [
            "review_id",
            "game_id",
            "title",
            "rating",
            "content",
            "image_url",
            "created_at",
            "updated_at",
            "actions",
        ]

    def get_actions(self, obj: Any) -> Any:
        return {
            "edit_url": f"/api/v1/reviews/{obj.review_id}",
            "delete_url": f"/api/v1/reviews/{obj.review_id}",
        }


class MyReviewListResponseSerializer(serializers.Serializer[Any]):
    status = serializers.CharField(read_only=True, default="success")
    total_reviews = serializers.IntegerField()
    page = serializers.IntegerField()
    limit = serializers.IntegerField()
    total_pages = serializers.IntegerField()
    reviews = MyReviewListSerializer(many=True)


class MyReviewListErrorSerializer(serializers.Serializer[Any]):
    detail = serializers.CharField()

    error_messages = {
        "invalid_page": "유효하지 않은 페이지 번호입니다.",
        "no_reviews": "작성한 리뷰가 없습니다.",
    }
