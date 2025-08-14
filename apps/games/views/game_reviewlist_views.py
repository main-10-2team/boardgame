from typing import Any, cast

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.games.serializers.game_review_list_serializer import (
    GameReviewListResponseSerializer,
    ReviewListSerializer,
)
from apps.users.models import User


class GameReviewListView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    serializer_class = ReviewListSerializer

    @extend_schema(
        summary="게임 리뷰 목록 조회",
        description="특정 게임의 리뷰 목록을 최신순으로 조회합니다. 페이지네이션을 지원합니다.",
        tags=["게임 리뷰"],
        parameters=[
            OpenApiParameter(
                name="game_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description="게임 ID",
            ),
            OpenApiParameter(
                name="page",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="페이지 번호",
                default=1,
            ),
            OpenApiParameter(
                name="limit",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="페이지당 리소스 수 (최대 10)",
                default=10,
            ),
        ],
        responses={
            200: ReviewListSerializer,
            400: {"description": "Bad Request", "example": {"detail": "유효하지 않은 게임 ID입니다."}},
            404: {"description": "Not Found", "example": {"detail": "리뷰가 존재하지 않습니다."}},
        },
    )
    def get(self, request: Request, game_id: int, *args: Any, **kwargs: Any) -> Response:
        user = cast(User, self.request.user)

        if user.is_authenticated and getattr(user, "status", "active") != "active":
            return Response(
                {"detail": "비활성화된 계정입니다. 관리자에게 문의하세요."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = {
            "game_id": game_id,
            "page": request.query_params.get("page", 1),
            "limit": request.query_params.get("limit", 10),
        }

        serializer = GameReviewListResponseSerializer(data=data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        response_data = serializer.get_response_data()
        return Response(response_data, status=status.HTTP_200_OK)
