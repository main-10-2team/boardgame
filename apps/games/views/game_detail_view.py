from typing import Any

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
)
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

    @extend_schema(
        summary="게임 상세 조회",
        description="특정 게임의 상세 정보를 조회합니다.",
        tags=["게임"],
        parameters=[
            OpenApiParameter(
                name="game_id",
                description="조회할 게임의 고유 ID",
                required=True,
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
            ),
        ],
        responses={
            200: GameDetailSerializer,
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Not Found",
                examples=[
                    OpenApiExample(
                        name="NotFound",
                        value={"detail": "게임을 찾을 수 없습니다."},
                        response_only=True,
                    )
                ],
            ),
        },
    )
    def get(self, request: Request, game_id: int, *args: Any, **kwargs: Any) -> Response:
        try:
            game = Game.objects.get(pk=game_id)
        except Game.DoesNotExist:
            return Response({"detail": "게임을 찾을 수 없습니다."}, status=HTTP_404_NOT_FOUND)

        serializer = GameDetailSerializer(game, context={"request": request})
        return Response(serializer.data)
