from rest_framework import serializers

from apps.games.models import Game, Like


class GameSearchSerializer(serializers.ModelSerializer[Game]):  # Game 모델 명시
    play_time = serializers.SerializerMethodField(method_name="get_playtime_minutes_formatted")
    is_liked = serializers.SerializerMethodField()

    class Meta:
        model = Game
        fields = [
            "game_id",
            "title",
            "thumbnail_url",
            "average_rating",
            "min_players",
            "max_players",
            "play_time",
            "is_liked",
        ]

    def get_playtime_minutes_formatted(self, obj: Game) -> str:
        if obj.playtime_min_minutes == obj.playtime_max_minutes:
            return f"{obj.playtime_min_minutes}분"
        return f"{obj.playtime_min_minutes}-{obj.playtime_max_minutes}분"

    def get_is_liked(self, obj: Game) -> bool:
        request = self.context.get("request")
        if request and hasattr(request, "user") and request.user.is_authenticated:
            if hasattr(obj, "is_liked_by_user"):
                return bool(obj.is_liked_by_user)
            return bool(Like.objects.filter(user=request.user, game=obj).exists())
        return False
