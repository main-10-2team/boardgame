from typing import Any

from rest_framework import serializers

from apps.games.models import Game, Review


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


class GameReviewListResponseSerializer(serializers.Serializer[Any]):
    game_id = serializers.IntegerField()
    page = serializers.IntegerField(default=1)
    limit = serializers.IntegerField(default=10)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        try:
            page = int(attrs.get("page", 1))
            limit = int(attrs.get("limit", 10))
        except ValueError:
            raise serializers.ValidationError({"detail": "page와 limit는 숫자여야 합니다."})

        if limit < 1:
            raise serializers.ValidationError({"detail": "limit는 1 이상이어야 합니다."})
        if page < 1:
            raise serializers.ValidationError({"detail": "page는 1 이상이어야 합니다."})

        game_id = attrs["game_id"]
        if not Game.objects.filter(game_id=game_id).exists():
            raise serializers.ValidationError({"detail": "유효하지 않은 게임 ID입니다."})

        attrs["page"] = page
        attrs["limit"] = min(limit, 10)
        return attrs

    def get_response_data(self) -> dict[str, Any]:
        game_id = self.validated_data["game_id"]
        page = self.validated_data["page"]
        limit = self.validated_data["limit"]

        reviews_qs = Review.objects.filter(game_id=game_id).select_related("user").order_by("-created_at")
        total_reviews = reviews_qs.count()

        if total_reviews == 0:
            raise serializers.ValidationError({"detail": "리뷰가 존재하지 않습니다."})

        total_pages = (total_reviews + limit - 1) // limit

        if page > total_pages:
            raise serializers.ValidationError({"detail": f"요청한 페이지는 존재하지 않습니다. (1 ~ {total_pages})"})

        offset = (page - 1) * limit
        reviews_page = reviews_qs[offset : offset + limit]
        reviews_data = ReviewListSerializer(reviews_page, many=True).data

        return {
            "status": "success",
            "game_id": game_id,
            "total_reviews": total_reviews,
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
            "reviews": reviews_data,
        }
