from typing import cast

from django.db.models import Exists, OuterRef
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.games.models import Category, Game, Genre, Like
from apps.games.serializers.game_list_serializer import (
    GameFilterSerializer,
    GameListSerializer,
)
from apps.users.models import User


class GameListView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]
    serializer_class = GameListSerializer

    @extend_schema(
        summary="게임 목록 조회 (검색 + 필터 + 정렬)",
        description="키워드 검색, 정렬, 필터링(인원수, 시간, 난이도, 테마(장르), 카테고리, 연령대 등)을 포함한 게임 목록 조회",
        tags=["게임"],
        parameters=[
            OpenApiParameter(name="sort_by", type=OpenApiTypes.STR, enum=["popularity", "rating", "latest", "review"]),
            OpenApiParameter(name="keyword", type=OpenApiTypes.STR),
            OpenApiParameter(name="players", type=OpenApiTypes.INT),
            OpenApiParameter(name="playtime_min_minutes", type=OpenApiTypes.INT),
            OpenApiParameter(name="playtime_max_minutes", type=OpenApiTypes.INT),
            OpenApiParameter(name="difficulty", type=OpenApiTypes.STR),
            OpenApiParameter(name="genres", type=OpenApiTypes.STR),
            OpenApiParameter(name="categories", type=OpenApiTypes.STR),
            OpenApiParameter(name="age", type=OpenApiTypes.INT),
            OpenApiParameter(name="page", type=OpenApiTypes.INT),
            OpenApiParameter(name="page_size", type=OpenApiTypes.INT),
        ],
        responses={200: GameListSerializer(many=True)},
    )
    def get(self, request: Request) -> Response:
        user = cast(User, request.user)
        queryset = Game.objects.all()

        filter_serializer = GameFilterSerializer(data=request.query_params)
        filter_serializer.is_valid(raise_exception=True)
        queryset = filter_serializer.filter_queryset(queryset)

        queryset = queryset.distinct()

        sort_by = request.query_params.get("sort_by", "popularity")
        sort_fields = {
            "popularity": "-like_count",
            "rating": "-average_rating",
            "latest": "-created_at",
            "review": "-reviews_count",
        }
        queryset = queryset.order_by(sort_fields.get(sort_by, "-like_count"))
        if user.is_authenticated:
            queryset = queryset.annotate(
                is_liked_by_user=Exists(Like.objects.filter(user_id=user.user_id, game=OuterRef("pk")))
            )

        # genre_rankings = {}
        # for genre in Genre.objects.all():
        #     genre_games = Game.objects.filter(game_genres__genre=genre).order_by("-like_count")[:5]
        #     genre_games = genre_games.annotate(is_liked_by_user=Exists(Like.objects.filter(game=OuterRef("pk"))))
        #     genre_rankings[genre.name] = self.serializer_class(
        #         genre_games, many=True, context={"request": request}
        #     ).data
        #
        # category_rankings = {}
        # for category in Category.objects.all():
        #     category_games = Game.objects.filter(categories__in=[category]).order_by("-like_count")[:5]
        #     category_games = category_games.annotate(is_liked_by_user=Exists(Like.objects.filter(game=OuterRef("pk"))))
        #     category_rankings[category.name] = self.serializer_class(
        #         category_games, many=True, context={"request": request}
        #     ).data

        paginator = PageNumberPagination()
        paginator.page_size = 12
        paginator.page_size_query_param = "page_size"
        page = paginator.paginate_queryset(queryset, request, view=self)

        serializer = self.serializer_class(page, many=True, context={"request": request})
        response = paginator.get_paginated_response(serializer.data)

        # response.data["genre_rankings"] = genre_rankings
        # response.data["category_rankings"] = category_rankings

        return response
