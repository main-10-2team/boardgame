from typing import Any, List

from django.db.models import QuerySet
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.games.models import Game
from apps.games.serializers.game_ranking_serializer import GameRankListSerializer


class GameRankListView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        summary="게임 랭킹 조회",
        description="좋아요 수 또는 평점 기준으로 상위 3개 게임을 조회합니다.",
        tags=["랭킹 목록 조회"],
        responses={
            200: OpenApiResponse(
                description="랭킹 게임 리스트 반환 성공",
                response=GameRankListSerializer(many=True),
            )
        },
    )
    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:

        top_liked_games: QuerySet[Game] = Game.objects.prefetch_related("detail_images").order_by("-like_count")[:3]
        top_rated_games: QuerySet[Game] = Game.objects.prefetch_related("detail_images").order_by("-average_rating")[:3]
        return Response(
            {
                "top_by_like": GameRankListSerializer(top_liked_games, many=True).data,
                "top_by_rating": GameRankListSerializer(top_rated_games, many=True).data,
            }
        )
