from rest_framework import serializers

from apps.games.models import Game


class GameFilterSerializer(serializers.ModelSerializer[Game]):
    game_id = serializers.IntegerField(source="pk")
    title = serializers.CharField()
    image_url = serializers.URLField(source="thumbnail_url")
    average_rating = serializers.FloatField()
    min_players = serializers.IntegerField()
    max_players = serializers.IntegerField()
    playtime_min_minutes = serializers.IntegerField()
    playtime_max_minutes = serializers.IntegerField()
    difficulty = serializers.SerializerMethodField()

    class Meta:
        model = Game
        fields = (
            "game_id",
            "title",
            "image_url",
            "average_rating",
            "min_players",
            "max_players",
            "playtime_min_minutes",
            "playtime_max_minutes",
            "difficulty",
        )

    def get_play_time(self, obj: Game) -> str:
        return f"{obj.playtime_min_minutes}~{obj.playtime_max_minutes}분"

    def get_difficulty(self, obj: Game) -> str:
        if obj.difficulty < 2:
            return "쉬움"
        elif obj.difficulty < 4:
            return "중급"
        else:
            return "어려움"
