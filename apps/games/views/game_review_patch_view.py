from django.db.models import Avg
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.games.models import Review
from apps.games.serializers.game_review_patch_serializer import (
    GameReviewPatchRequestSerializer,
    ReviewPatchResponseReviewSerializer,
)


class GameReviewPatchAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        summary="리뷰 수정",
        description="로그인한 사용자가 본인이 작성한 리뷰를 수정합니다. 평점 또는 내용을 선택적으로 수정할 수 있습니다.",
        tags=["게임 리뷰"],
        request=GameReviewPatchRequestSerializer,
        responses={
            200: OpenApiExample(
                "성공 응답",
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
                status_codes=["200"],
            ),
            400: OpenApiExample(
                "잘못된 요청 에러",
                value={"detail": "유효하지 않은 평점입니다."},
                response_only=True,
                status_codes=["400"],
            ),
            401: OpenApiExample(
                "인증 에러",
                value={"detail": "JWT 토큰이 유효하지 않거나 만료된 경우"},
                response_only=True,
                status_codes=["401"],
            ),
            403: OpenApiExample(
                "권한 없음 에러",
                value={"detail": "본인의 리뷰만 수정할 수 있습니다."},
                response_only=True,
                status_codes=["403"],
            ),
            404: OpenApiExample(
                "리뷰를 찾을 수 없음 에러",
                value={"detail": "리뷰를 찾을 수 없습니다."},
                response_only=True,
                status_codes=["404"],
            ),
        },
    )
    def patch(self, request: Request, review_id: int) -> Response:
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

        updated_review = serializer.save()

        average_rating = (
            Review.objects.filter(game=updated_review.game).aggregate(avg_rating=Avg("rating")).get("avg_rating")
        )

        average_rating = round(average_rating or 0.0, 2)

        game = updated_review.game
        game.average_rating = average_rating
        game.save(update_fields=["average_rating"])

        response_serializer = ReviewPatchResponseReviewSerializer(review)

        response_data = {
            "status": "success",
            "message": "리뷰가 성공적으로 수정되었습니다.",
            "review": response_serializer.data,
            "updated_average_rating": review.game.average_rating,
        }

        return Response(response_data, status=status.HTTP_200_OK)
