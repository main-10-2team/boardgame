from typing import Optional

from rest_framework import serializers

from apps.games.models import Game, GameImage, Like, Review


class GameImageSerializer(serializers.ModelSerializer[GameImage]):
    class Meta:
        model = GameImage
        fields = ["game_des_img_url"]


class GameDetailSerializer(serializers.ModelSerializer[Game]):
    game_id = serializers.IntegerField(source="pk", read_only=True)
    review_count = serializers.IntegerField(source="reviews_count", read_only=True)
    play_time = serializers.SerializerMethodField()
    is_like = serializers.SerializerMethodField()
    user_rated = serializers.SerializerMethodField()
    user_rating = serializers.SerializerMethodField()
    game_images = GameImageSerializer(source="detail_images", many=True, read_only=True)

    class Meta:
        model = Game
        fields = [
            "game_id",
            "title",
            "description",
            "thumbnail_url",
            "min_players",
            "max_players",
            "play_time",
            "difficulty",
            "average_rating",
            "review_count",
            "is_like",
            "user_rated",
            "user_rating",
            "game_images",
        ]
        read_only_fields = fields

    def get_play_time(self, obj: Game) -> str:
        return f"{obj.playtime_min_minutes}–{obj.playtime_max_minutes}분"

    def get_is_like(self, obj: Game) -> bool:
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return Like.objects.filter(user=request.user, game=obj).exists()
        return False

    def get_user_rated(self, obj: Game) -> bool:
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return Review.objects.filter(user=request.user, game=obj).exists()
        return False

    def get_user_rating(self, obj: Game) -> Optional[float]:
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            try:
                review = Review.objects.get(user=request.user, game=obj)
                return review.rating
            except Review.DoesNotExist:
                return None
        return None
