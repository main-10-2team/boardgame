from typing import Any

from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.status import HTTP_404_NOT_FOUND
from rest_framework.views import APIView

from apps.games.models import Game
from apps.games.serializers.game_detail_serializer import GameDetailSerializer


class GameDetailView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    serializer_class = GameDetailSerializer

    @extend_schema(
        summary="게임 상세 조회",
        description="특정 게임의 상세 정보를 조회합니다.",
        parameters=[
            OpenApiParameter(
                name="game_id",
                description="조회할 게임의 고유 ID",
                required=True,
                type=int,
                location="path",
            )
        ],
        responses={
            200: GameDetailSerializer,
            404: OpenApiParameter(name="detail", description="게임을 찾을 수 없습니다.", required=False, type=str),
        },
        tags=["게임"],
    )
    def get(self, request: Request, game_id: int, *args: Any, **kwargs: Any) -> Response:
        try:
            game = Game.objects.get(pk=game_id)
        except Game.DoesNotExist:
            return Response({"detail": "게임을 찾을 수 없습니다."}, status=HTTP_404_NOT_FOUND)

        serializer = GameDetailSerializer(game, context={"request": request})
        return Response(serializer.data)

