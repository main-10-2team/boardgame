from typing import Any, cast

from django.db.models import Avg
from rest_framework import serializers

from apps.games.models import Review


class ReviewDeleteSerializer(serializers.ModelSerializer[Review]):
    class Meta:
        model = Review
        fields = ["id"]

    default_error_messages = {
        "invalid_review_id": "유효하지 않은 리뷰 ID입니다.",
        "not_author": "본인의 리뷰만 삭제할 수 있습니다.",
        "review_not_found": "리뷰를 찾을 수 없습니다.",
    }

    def save(self, **kwargs: Any) -> Review:
        review = cast(Review, self.instance)
        if review is None:
            self.fail("review_not_found")

        self._game_id = review.game_id
        self._review_id = review.review_id
        game = review.game

        review.delete()

        reviews = Review.objects.filter(game=game)
        average_rating = reviews.aggregate(avg_rating=Avg("rating"))["avg_rating"] or 0.0
        game.average_rating = round(average_rating, 2)
        game.reviews_count = reviews.count()
        game.save(update_fields=["average_rating", "reviews_count", "updated_at"])

        user = review.user
        user.review_count = user.reviews.count()
        user.save(update_fields=["review_count"])

        self._updated_average_rating = game.average_rating
        self._updated_review = review

        return review

    def to_representation(self, instance: Any) -> dict[str, Any]:
        return {
            "status": "success",
            "message": "리뷰가 성공적으로 삭제되었습니다.",
            "game_id": self._game_id,
            "review_id": self._review_id,
            "updated_average_rating": self._updated_average_rating,
            "remove_from_list": True,
        }


class ReviewDeleteResponseSerializer(serializers.Serializer[Any]):
    status: serializers.CharField = serializers.CharField()
    message: serializers.CharField = serializers.CharField()
    game_id: serializers.IntegerField = serializers.IntegerField()
    review_id: serializers.IntegerField = serializers.IntegerField()
    updated_average_rating: serializers.FloatField = serializers.FloatField()
    remove_from_list: serializers.BooleanField = serializers.BooleanField()
