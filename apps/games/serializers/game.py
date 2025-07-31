from rest_framework import serializers
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from apps.games.models import Game, Like


class GameSerializer(serializers.ModelSerializer[Game]):
    playtime_minutes = serializers.SerializerMethodField()
    genre_name = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()

    class Meta:
        model = Game
        fields = [
            "game_id",
            "age",
            "title",
            "description",
            "min_players",
            "max_players",
            "playtime_minutes",
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
            return f"{obj.playtime_min_minutes}min"
        return f"{obj.playtime_min_minutes}-{obj.playtime_max_minutes}min"

    def get_genre_name(self, obj: Game) -> str:
        genres = obj.game_genres.all().select_related("genre")
        return ", ".join([g.genre.name for g in genres])

    def get_is_liked(self, obj: Game) -> bool:
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return Like.objects.filter(user=request.user, game=obj).exists()
        return False
