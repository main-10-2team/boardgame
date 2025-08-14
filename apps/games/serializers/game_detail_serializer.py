from typing import Optional

from rest_framework import serializers

from apps.games.models import Game, GameImage, Like, Review

#
# class GameImageSerializer(serializers.ModelSerializer[GameImage]):
#     class Meta:
#         model = GameImage
#         fields = ["game_des_img_url"]


class GameDetailSerializer(serializers.ModelSerializer[Game]):
    game_id = serializers.IntegerField(source="pk", read_only=True)
    reviews_count = serializers.IntegerField(read_only=True)
    play_time = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    # user_rated = serializers.SerializerMethodField()
    user_rating = serializers.SerializerMethodField()
    genre_name = serializers.SerializerMethodField()
    category_name = serializers.SerializerMethodField()
    like_count = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(read_only=True)

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
            "reviews_count",
            "is_liked",
            "like_count",
            "user_rating",
            "age",
            "genre_name",
            "category_name",
            "created_at",
        ]
        read_only_fields = fields

    def get_play_time(self, obj: Game) -> str:
        return f"{obj.playtime_min_minutes}–{obj.playtime_max_minutes}분"

    def get_is_liked(self, obj: Game) -> bool:
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return Like.objects.filter(user=request.user, game=obj).exists()
        return False

    # def get_user_rated(self, obj: Game) -> bool:
    #     request = self.context.get("request")
    #     if request and request.user.is_authenticated:
    #         return Review.objects.filter(user=request.user, game=obj).exists()
    #     return False

    def get_user_rating(self, obj: Game) -> Optional[float]:
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            try:
                review = Review.objects.get(user=request.user, game=obj)
                return review.rating
            except Review.DoesNotExist:
                return None
        return None

    def get_genre_name(self, obj: Game) -> str:
        return ", ".join([genre.name for genre in obj.genres.all()])

    def get_category_name(self, obj: Game) -> str:
        return ", ".join([cat.name for cat in obj.categories.all()])

    def get_like_count(self, obj: Game) -> int:
        return obj.liked_by_users.count()
