from typing import Any, cast

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.games.models import Game, Review
from apps.games.serializers.review_list_serializer import ReviewListSerializer
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

        try:
            page = int(request.query_params.get("page", 1))
            limit = int(request.query_params.get("limit", 10))
        except ValueError:
            return Response({"detail": "page 및 limit는 정수여야 합니다."}, status=status.HTTP_400_BAD_REQUEST)

        if limit < 1:
            return Response({"detail": "limit는 1 이상이어야 합니다."}, status=status.HTTP_400_BAD_REQUEST)

        limit = min(limit, 10)

        if not Game.objects.filter(game_id=game_id).exists():
            return Response({"detail": "유효하지 않은 게임 ID입니다."}, status=status.HTTP_400_BAD_REQUEST)

        reviews_qs = Review.objects.filter(game_id=game_id).select_related("user").order_by("-created_at")
        total_reviews = reviews_qs.count()

        if total_reviews == 0:
            return Response({"detail": "리뷰가 존재하지 않습니다."}, status=status.HTTP_404_NOT_FOUND)

        reviews_per_page = limit
        total_pages = total_reviews // reviews_per_page
        if total_reviews % reviews_per_page != 0:
            total_pages += 1

        if page < 1 or page > total_pages:
            return Response(
                {"detail": f"요청한 페이지는 존재하지 않습니다. (1 ~ {total_pages})"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        offset = (page - 1) * reviews_per_page
        reviews_page = reviews_qs[offset : offset + reviews_per_page]

        serializer = ReviewListSerializer(reviews_page, many=True)

        return Response(
            {
                "status": "success",
                "game_id": game_id,
                "total_reviews": total_reviews,
                "page": page,
                "limit": limit,
                "total_pages": total_pages,
                "reviews": serializer.data,
            },
            status=status.HTTP_200_OK,
        )
