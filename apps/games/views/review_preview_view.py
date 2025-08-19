from typing import Any

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.games.models import Review
from apps.games.serializers.review_preview_serializer import ReviewPreviewSerializer


class ReviewPreviewView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        summary="지금 뜨는 리뷰 목록",
        description="최신 리뷰 3개를 반환합니다. 게임명, 게임 ID, 유저 닉네임, 평점, 리뷰 내용, 게임 이미지가 포함됩니다.",
        tags=["지금 뜨는 리뷰"],
        responses={
            200: OpenApiResponse(
                description="리뷰 미리보기 리스트",
                response=ReviewPreviewSerializer(many=True),
            )
        },
    )
    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        latest_reviews = (
            Review.objects.select_related("user", "game")
            .prefetch_related("game__detail_images")
            .order_by("-created_at")
        )
        serializer = ReviewPreviewSerializer(latest_reviews, many=True)
        return Response(serializer.data)
