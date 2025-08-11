from typing import cast

from django.db.models import Avg
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
)
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.games.models import Review
from apps.games.serializers.game_review_delete_serializer import (
    ReviewDeleteResponseSerializer,
    ReviewDeleteSerializer,
)
from apps.users.models import User


class GameReviewDeleteAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        summary="리뷰 삭제",
        tags=["게임 리뷰"],
        description="로그인한 사용자가 본인이 작성한 리뷰를 삭제합니다.",
        parameters=[
            OpenApiParameter(
                name="review_id",
                type=OpenApiTypes.INT,
                location="path",
                description="리뷰 ID",
                required=True,
            )
        ],
        responses={
            200: ReviewDeleteResponseSerializer,
            401: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                examples=[
                    OpenApiExample(
                        "인증 에러",
                        value={"detail": "인증 토큰이 유효하지 않습니다."},
                        response_only=True,
                    )
                ],
            ),
            403: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                examples=[
                    OpenApiExample(
                        "권한 없음 에러",
                        value={"detail": "본인의 리뷰만 삭제할 수 있습니다."},
                        response_only=True,
                    )
                ],
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                examples=[
                    OpenApiExample(
                        "리뷰를 찾을 수 없음 에러",
                        value={"detail": "리뷰를 찾을 수 없습니다."},
                        response_only=True,
                    )
                ],
            ),
        },
    )
    def delete(self, request: Request, review_id: int) -> Response:
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
            review = Review.objects.get(pk=review_id)
        except Review.DoesNotExist:
            return Response(
                {"detail": ReviewDeleteSerializer().error_messages["review_not_found"]},
                status=status.HTTP_404_NOT_FOUND,
            )

        if review.user_id != user.user_id:
            return Response(
                {"detail": ReviewDeleteSerializer().error_messages["not_author"]},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = ReviewDeleteSerializer(instance=review)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)
