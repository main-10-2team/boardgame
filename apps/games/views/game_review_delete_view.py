from typing import cast

from django.db.models import Avg
from drf_spectacular.utils import OpenApiExample, extend_schema
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
        description="""로그인한 사용자가 본인이 작성한 리뷰를 삭제합니다.""",
        responses={
            200: ReviewDeleteResponseSerializer,
            401: OpenApiExample(
                "인증 에러",
                value={"detail": "인증 토큰이 유효하지 않습니다."},
                response_only=True,
                status_codes=["401"],
            ),
            403: OpenApiExample(
                "권한 없음 에러",
                value={"detail": "본인의 리뷰만 삭제할 수 있습니다."},
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
    def delete(self, request: Request, review_id: int) -> Response:
        try:
            review = Review.objects.get(pk=review_id)
        except Review.DoesNotExist:
            return Response(
                {"detail": ReviewDeleteSerializer().error_messages["review_not_found"]},
                status=status.HTTP_404_NOT_FOUND,
            )

        user = cast(User, request.user)
        if not user.is_authenticated:
            return Response(
                {"detail": "로그인이 필요합니다."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if review.user_id != user.user_id:
            return Response(
                {"detail": ReviewDeleteSerializer().error_messages["not_author"]},
                status=status.HTTP_403_FORBIDDEN,
            )

        game = review.game
        game_id = review.game_id
        review_id = review.review_id

        review.delete()

        reviews = Review.objects.filter(game=game)
        average_rating = reviews.aggregate(Avg("rating"))["rating__avg"] or 0.0
        game.average_rating = round(average_rating, 2)
        game.reviews_count = reviews.count()
        game.save(update_fields=["average_rating", "reviews_count", "updated_at"])

        user.review_count = user.reviews.count()
        user.save(update_fields=["review_count"])

        response_data = {
            "status": "success",
            "message": "리뷰가 성공적으로 삭제되었습니다.",
            "game_id": game_id,
            "review_id": review_id,
            "updated_average_rating": game.average_rating,
            "remove_from_list": True,
        }

        return Response(response_data, status=status.HTTP_200_OK)
