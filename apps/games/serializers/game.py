from rest_framework import serializers

from apps.games.models import Game, Like


class GameSerializer(serializers.ModelSerializer[Game]):
    genre_name = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    # play_time = serializers.SerializerMethodField(method_name="get_playtime_minutes_formatted")

    class Meta:
        model = Game
        fields = [
            "game_id",
            "age",
            "title",
            "description",
            "min_players",
            "max_players",
            "playtime_min_minutes",
            "playtime_max_minutes",
            "difficulty",
            "thumbnail_url",
            "rules_url",
            "genre_name",
            "average_rating",
            "created_at",
            "updated_at",
            "like_count",
            "reviews_count",
            "is_liked",
        ]

    def get_playtime_minutes(self, obj: Game) -> str:
        if obj.playtime_min_minutes == obj.playtime_max_minutes:
            return f"{obj.playtime_min_minutes}분"
        return f"{obj.playtime_min_minutes}-{obj.playtime_max_minutes}분"

    def get_genre_name(self, obj: Game) -> str:
        genres = obj.game_genres.all().select_related("genre")
        return ", ".join([g.genre.name for g in genres])

    # def get_is_liked(self, obj: Game) -> bool:
    #     request = self.context.get("request")
    #     if request and request.user.is_authenticated:
    #         return Like.objects.filter(user=request.user, game=obj).exists()
    #     return False

    def get_is_liked(self, obj: Game) -> bool:
        request = self.context.get("request")
        if request and hasattr(request, "user") and request.user.is_authenticated:
            if hasattr(obj, "is_liked_by_user"):
                return bool(obj.is_liked_by_user)
            return bool(Like.objects.filter(user=request.user, game=obj).exists())
        return False
