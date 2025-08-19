from typing import Optional

from rest_framework import serializers

from apps.games.models import Game, GameImage, Review


class ReviewPreviewSerializer(serializers.ModelSerializer[Review]):
    nickname = serializers.CharField(source="user.nickname", read_only=True)
    rating = serializers.FloatField()
    content = serializers.CharField()
    game_title = serializers.CharField(source="game.title", read_only=True)
    game_id = serializers.IntegerField(source="game.pk", read_only=True)
    images = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = [
            "game_id",
            "nickname",
            "rating",
            "content",
            "images",
            "game_title",
            "created_at",
        ]

    def get_images(self, obj: Review) -> Optional[str]:
        first: Optional[GameImage] = obj.game.detail_images.first()
        return first.game_des_img_url if first else obj.game.thumbnail_url
