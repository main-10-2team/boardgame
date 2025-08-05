from typing import Any

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


class ReviewDeleteResponseSerializer(serializers.Serializer[Any]):
    status: serializers.CharField = serializers.CharField()
    message: serializers.CharField = serializers.CharField()
    game_id: serializers.IntegerField = serializers.IntegerField()
    review_id: serializers.IntegerField = serializers.IntegerField()
    updated_average_rating: serializers.FloatField = serializers.FloatField()
    remove_from_list: serializers.BooleanField = serializers.BooleanField()
