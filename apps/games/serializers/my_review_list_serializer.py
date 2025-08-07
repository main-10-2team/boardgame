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

    def to_representation(self, instance: Any) -> Dict[str, Any]:
        page = self.context["page"]
        limit = self.context["limit"]
        paginator = self.context["paginator"]

        serialized_reviews = MyReviewListSerializer(instance, many=True).data

        return {
            "status": "success",
            "message": "리뷰 목록을 성공적으로 불러왔습니다.",
            "total_reviews": paginator.count,
            "page": page,
            "limit": limit,
            "total_pages": paginator.num_pages,
            "reviews": serialized_reviews,
        }


class MyReviewListErrorSerializer(serializers.Serializer[Any]):
    detail = serializers.CharField()

    error_messages = {
        "invalid_page": "유효하지 않은 페이지 번호입니다.",
        "no_reviews": "작성한 리뷰가 없습니다.",
    }
