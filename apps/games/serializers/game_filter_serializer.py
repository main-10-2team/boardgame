from typing import Any, Tuple

from django.db.models.query import QuerySet
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

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

    def get_difficulty(self, obj: Game) -> float:
        return round(obj.difficulty, 2)

    def filter_queryset(self) -> Tuple[QuerySet[Game], dict[str, Any]]:
        params = self.context["request"].query_params
        queryset = Game.objects.all()
        applied_filters: dict[str, Any] = {
            "players": None,
            "play_time": None,
            "difficulty": None,
        }

        players_param = params.get("players")
        if players_param:
            try:
                players = int(players_param)
                if players < 1:
                    raise ValidationError({"detail": "플레이어 수는 1 이상이어야 합니다."})
                queryset = queryset.filter(min_players__lte=players, max_players__gte=players)
                applied_filters["players"] = players
            except ValueError:
                raise ValidationError({"detail": "플레이어 수는 숫자여야 합니다. 예: 2, 4, 6 등"})

        playtime_min = params.get("playtime_min_minutes")
        playtime_max = params.get("playtime_max_minutes")

        if playtime_min:
            try:
                playtime_min = int(playtime_min)
                queryset = queryset.filter(playtime_min_minutes__gte=playtime_min)
            except ValueError:
                raise ValidationError({"detail": "최소 플레이 시간이 유효하지 않습니다."})

        if playtime_max:
            try:
                playtime_max = int(playtime_max)
                queryset = queryset.filter(playtime_max_minutes__lte=playtime_max)
            except ValueError:
                raise ValidationError({"detail": "최대 플레이 시간이 유효하지 않습니다."})

        difficulty_param = params.get("difficulty")
        difficulty_map = {
            "쉬움": (0.0, 2.0),
            "중급": (2.0, 4.0),
            "어려움": (4.0, 5.0),
        }

        if difficulty_param:
            if difficulty_param in difficulty_map:
                lower, upper = difficulty_map[difficulty_param]
                queryset = queryset.filter(difficulty__gte=lower, difficulty__lt=upper)
                applied_filters["difficulty"] = difficulty_param
            else:
                try:
                    diff = float(difficulty_param)
                    if 0.0 <= diff <= 5.0:
                        lower = round(diff - 0.5, 1)
                        upper = round(diff + 0.5, 1)
                        queryset = queryset.filter(difficulty__gte=lower, difficulty__lt=upper)
                        applied_filters["difficulty"] = str(diff)
                    else:
                        raise ValueError
                except ValueError:
                    raise ValidationError({"detail": "난이도는 '쉬움', '중급', '어려움' 중 하나 또는 숫자여야 합니다."})

        return queryset, applied_filters
