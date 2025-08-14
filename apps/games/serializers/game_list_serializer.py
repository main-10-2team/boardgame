from typing import Any

from django.db.models import QuerySet
from rest_framework import serializers

from apps.games.models import Game, Like


class GameListSerializer(serializers.ModelSerializer[Game]):
    genre = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()

    class Meta:
        model = Game
        fields = [
            "game_id",
            "title",
            "thumbnail_url",
            "difficulty",
            "average_rating",
            "like_count",
            "reviews_count",
            "genre",
            "category",
            "is_liked",
        ]

    def get_genre(self, obj: Game) -> str:
        return ", ".join([genre.name for genre in obj.genres.all()])

    def get_category(self, obj: Game) -> str:
        return ", ".join([cat.name for cat in obj.categories.all()])

    # def get_play_time(self, obj: Game) -> str:
    #     if obj.playtime_min_minutes == obj.playtime_max_minutes:
    #         return f"{obj.playtime_min_minutes}분"
    #     return f"{obj.playtime_min_minutes}-{obj.playtime_max_minutes}분"

    def get_difficulty(self, obj: Game) -> str:  # 👈 여기 추가
        if obj.difficulty < 2.0:
            return "쉬움"
        elif obj.difficulty < 4.0:
            return "중급"
        else:
            return "어려움"


    def get_is_liked(self, obj: Game) -> bool:
        request = self.context.get("request")
        if request and hasattr(request, "user") and request.user.is_authenticated:
            if hasattr(obj, "is_liked_by_user"):
                return bool(obj.is_liked_by_user)
            return Like.objects.filter(user=request.user, game=obj).exists()
        return False


class GameFilterSerializer(serializers.Serializer[Any]):
    keyword = serializers.CharField(required=False, allow_blank=True)
    players = serializers.IntegerField(required=False, min_value=1)
    playtime_min_minutes = serializers.IntegerField(required=False, min_value=0)
    playtime_max_minutes = serializers.IntegerField(required=False, min_value=0)
    difficulty = serializers.CharField(required=False)
    genres = serializers.CharField(required=False)
    categories = serializers.CharField(required=False)
    age = serializers.IntegerField(required=False, min_value=0)

    def filter_queryset(self, queryset: QuerySet[Game]) -> QuerySet[Game]:
        data = self.validated_data

        keyword = data.get("keyword")
        if keyword:
            queryset = queryset.filter(title__icontains=keyword)

        players = data.get("players")
        if players:
            queryset = queryset.filter(min_players__lte=players, max_players__gte=players)

        if "playtime_min_minutes" in data:
            queryset = queryset.filter(playtime_min_minutes__gte=data["playtime_min_minutes"])

        if "playtime_max_minutes" in data:
            queryset = queryset.filter(playtime_max_minutes__lte=data["playtime_max_minutes"])

        difficulty = data.get("difficulty")
        if difficulty:
            diff_map = {"쉬움": (0.0, 2.0), "중급": (2.0, 4.0), "어려움": (4.0, 5.0)}
            if difficulty in diff_map:
                low, high = diff_map[difficulty]
                queryset = queryset.filter(difficulty__gte=low, difficulty__lt=high)
            else:
                # try:
                #     p = float(difficulty)
                #     queryset = queryset.filter(difficulty__gte=p - 0.5, difficulty__lte=p + 0.5)
                # except ValueError:
                raise serializers.ValidationError(
                    {"difficulty": "난이도는 '쉬움', '중급', '어려움' 또는 숫자입니다."}
                )

        genres = data.get("genres")
        if genres:
            genre_list = [g.strip() for g in genres.split(",")]
            queryset = queryset.filter(genres__name__in=genre_list).distinct()

        categories = data.get("categories")
        if categories:
            category_list = [c.strip() for c in categories.split(",")]
            queryset = queryset.filter(categories__name__in=category_list).distinct()

        age = data.get("age")
        if age:
            queryset = queryset.filter(age__lte=age)

        return queryset
