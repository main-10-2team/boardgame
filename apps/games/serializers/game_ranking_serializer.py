from rest_framework import serializers

from apps.games.models import Game, GameImage


class GameRankListSerializer(serializers.ModelSerializer[Game]):
    game_id = serializers.IntegerField()
    like_count = serializers.IntegerField()
    average_rating = serializers.FloatField()
    genre = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()
    difficulty = serializers.SerializerMethodField()

    class Meta:
        model = Game
        fields = [
            "game_id",
            "thumbnail_url",
            "title",
            "description",
            "like_count",
            "average_rating",
            "genre",
            "category",
            "difficulty",
        ]

    def get_genre(self, obj: Game) -> str:
        return ", ".join([genre.name for genre in obj.genres.all()])

    def get_category(self, obj: Game) -> str:
        return ", ".join([cat.name for cat in obj.categories.all()])

    def get_difficulty(self, obj: Game) -> str:  # 👈 여기 추가
        if obj.difficulty < 2.0:
            return "쉬움"
        elif obj.difficulty < 4.0:
            return "중급"
        else:
            return "어려움"
