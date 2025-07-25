from django.db.models import Exists, OuterRef
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.games.models import Game, Like
from apps.games.serializers.gameserializer import GameSerializer


class GameListView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    serializer_class = GameSerializer

    @extend_schema(
        summary="게임 목록 조회",
        description="게임 목록을 정렬 기준(popularity, rating, latest)에 따라 조회합니다.",
        tags=["게임"],
        parameters=[
            OpenApiParameter(
                name="sort_by",
                description="정렬 기준: popularity(인기순), rating(평점순), latest(최신순)",
                required=False,
                type=OpenApiTypes.STR,
                enum=["popularity", "rating", "latest"],
            )
        ],
        responses={200: GameSerializer(many=True), 400: OpenApiTypes.OBJECT},
    )
    def get(self, request: Request) -> Response:
        sort_by = request.query_params.get("sort_by", "popularity")

        valid_sort_fields = {
            "popularity": "-like_count",
            "rating": "-average_rating",
            "latest": "-created_at",
        }

        if sort_by not in valid_sort_fields:
            return Response({"detail": "유효하지 않은 정렬 기준입니다."}, status=status.HTTP_400_BAD_REQUEST)

        order_by_field = valid_sort_fields[sort_by]

        games_queryset = Game.objects.all().prefetch_related("gamegenre_set__genre").order_by(order_by_field)

        if request.user.is_authenticated:
            games_queryset = games_queryset.annotate(
                is_liked_by_user=Exists(Like.objects.filter(user=request.user, game=OuterRef("pk")))
            )

        paginator = PageNumberPagination()
        paginator.page_size_query_param = "page_size"

        paginated_games = paginator.paginate_queryset(games_queryset, request, view=self)

        if paginated_games is None:
            return paginator.get_paginated_response([])

        serializer = self.serializer_class(paginated_games, many=True, context={"request": request})

        return paginator.get_paginated_response(serializer.data)
