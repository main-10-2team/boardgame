from typing import cast

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiResponse,
    extend_schema,
    inline_serializer,
)
from rest_framework import serializers, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.games.models import Review
from apps.games.serializers.game_review_patch_serializer import (
    GameReviewPatchRequestSerializer,
)
from apps.users.models import User

unauth_schema = inline_serializer(name="UnauthorizedError_GameReviewPatch", fields={"detail": serializers.CharField()})


class GameReviewPatchAPIView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        summary="리뷰 수정",
        description="로그인한 사용자가 본인이 작성한 리뷰를 수정합니다. 평점 또는 내용을 선택적으로 수정할 수 있습니다.",
        tags=["게임 리뷰"],
        request=GameReviewPatchRequestSerializer,
        responses={
            200: OpenApiResponse(
                response=inline_serializer(
                    name="GameReviewPatchSuccess",
                    fields={
                        "status": serializers.CharField(),
                        "message": serializers.CharField(),
                        "review": inline_serializer(
                            name="PatchedReview",
                            fields={
                                "review_id": serializers.IntegerField(),
                                "game_id": serializers.IntegerField(),
                                "user_id": serializers.IntegerField(),
                                "nickname": serializers.CharField(),
                                "rating": serializers.FloatField(),
                                "content": serializers.CharField(),
                                "created_at": serializers.DateTimeField(),
                                "updated_at": serializers.DateTimeField(),
                            },
                        ),
                        "updated_average_rating": serializers.FloatField(),
                    },
                ),
                examples=[
                    OpenApiExample(
                        name="성공 응답",
                        value={
                            "status": "success",
                            "message": "리뷰가 성공적으로 수정되었습니다.",
                            "review": {
                                "review_id": 1,
                                "game_id": 123,
                                "user_id": 1,
                                "nickname": "BoardGameFan",
                                "rating": 4.0,
                                "content": "수정된 리뷰: 전략이 더 깊이 있는 게임임!",
                                "created_at": "2025-07-23T15:00:00Z",
                                "updated_at": "2025-07-23T16:21:00Z",
                            },
                            "updated_average_rating": 4.30,
                        },
                        response_only=True,
                    )
                ],
            ),
            401: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Unauthorized",
                examples=[
                    OpenApiExample(
                        "Unauthorized", value={"detail": "인증 토큰이 유효하지 않습니다."}, response_only=True
                    )
                ],
            ),
            403: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Forbidden",
                examples=[
                    OpenApiExample(
                        "Forbidden", value={"detail": "본인의 리뷰만 수정할 수 있습니다."}, response_only=True
                    )
                ],
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Not Found",
                examples=[
                    OpenApiExample("Not Found", value={"detail": "리뷰를 찾을 수 없습니다."}, response_only=True)
                ],
            ),
        },
    )
    def patch(self, request: Request, review_id: int) -> Response:
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
            review = Review.objects.select_related("user", "game").get(review_id=review_id)
        except Review.DoesNotExist:
            return Response({"detail": "리뷰를 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

        if review.user != request.user:
            return Response(
                {"detail": "본인의 리뷰만 수정할 수 있습니다."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = GameReviewPatchRequestSerializer(data=request.data, partial=True, instance=review)
        serializer.is_valid(raise_exception=True)

        if not serializer.validated_data:
            return Response(
                {"detail": "rating, content 중 하나 누락된 됬습니다"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)
