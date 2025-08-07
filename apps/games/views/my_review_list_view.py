from typing import Any, cast

from django.core.paginator import EmptyPage, Paginator
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.games.models import Review
from apps.games.serializers.my_review_list_serializer import (
    MyReviewListErrorSerializer,
    MyReviewListResponseSerializer,
    MyReviewListSerializer,
)
from apps.users.models import User


class MyReviewListView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        summary="내 리뷰 목록 조회",
        tags=["게임 리뷰"],
        description="로그인한 사용자가 자신이 작성한 리뷰 목록을 조회합니다.",
        parameters=[
            OpenApiParameter(
                name="page",
                type=int,
                location=OpenApiParameter.QUERY,
                required=False,
                description="조회할 페이지 번호 (기본값: 1)",
            ),
            OpenApiParameter(
                name="limit",
                type=int,
                location=OpenApiParameter.QUERY,
                required=False,
                description="페이지당 리뷰 수 (기본값: 10, 최대: 10)",
            ),
        ],
        responses={
            200: MyReviewListResponseSerializer,
            400: MyReviewListErrorSerializer,
            401: OpenApiExample(
                "Unauthorized",
                value={"detail": "인증 토큰이 유효하지 않습니다."},
                response_only=True,
                status_codes=["401"],
            ),
            404: MyReviewListErrorSerializer,
        },
    )
    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        user = cast(User, request.user)

        if not user.is_authenticated:
            return Response(
                {"detail": "로그인이 필요합니다."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if user.status != "active":
            return Response(
                {"detail": "비활성화된 계정입니다. 관리자에게 문의하세요."}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            page = int(request.query_params.get("page", 1))
            limit = min(int(request.query_params.get("limit", 10)), 10)
        except ValueError:
            return Response(
                {"detail": MyReviewListErrorSerializer.error_messages["invalid_page"]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        reviews = Review.objects.select_related("game").filter(user=user).order_by("-created_at")

        if not reviews.exists():
            return Response(
                {"detail": MyReviewListErrorSerializer.error_messages["no_reviews"]}, status=status.HTTP_404_NOT_FOUND
            )

        paginator = Paginator(reviews, limit)

        try:
            page_obj = paginator.page(page)
        except EmptyPage:
            return Response(
                {"detail": MyReviewListErrorSerializer.error_messages["invalid_page"]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        response_serializer = MyReviewListResponseSerializer(
            page_obj, context={"page": page, "limit": limit, "paginator": paginator}
        )

        return Response(response_serializer.data, status=status.HTTP_200_OK)
