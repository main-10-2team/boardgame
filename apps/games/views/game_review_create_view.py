from typing import Any, cast

from django.db.models import Avg
from django.utils.timezone import now
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiResponse,
    extend_schema,
    inline_serializer,
)
from rest_framework import serializers, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.games.models import Review
from apps.games.serializers.game_review_create_serializer import (
    GameReviewCreateResponseSerializer,
    GameReviewCreateSerializer,
)
from apps.users.models import User


class GameReviewCreateView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    serializer_class = GameReviewCreateSerializer

    @extend_schema(
        summary="리뷰 작성",
        description="로그인한 사용자가 특정 게임에 대한 리뷰를 작성합니다.",
        tags=["게임 리뷰"],
        request=GameReviewCreateSerializer,
        responses={
            201: OpenApiResponse(
                response=GameReviewCreateResponseSerializer,
                examples=[
                    OpenApiExample(
                        name="성공 응답",
                        value={
                            "status": "success",
                            "message": "리뷰가 성공적으로 작성되었습니다.",
                            "game_id": 123,
                            "review": {
                                "review_id": 1,
                                "user_id": 1,
                                "nickname": "BoardGameFan",
                                "rating": 4.5,
                                "content": "정말 재미있는 게임! 전략적인 요소가 강력함.",
                                "created_at": "2025-07-23T15:53:00Z",
                            },
                            "updated_average_rating": 4.25,
                            "refresh_page": True,
                        },
                        response_only=True,
                    )
                ],
            ),
            400: OpenApiResponse(
                response=inline_serializer(
                    name="GameReviewCreateBadRequest",
                    fields={"detail": serializers.CharField()},
                ),
                examples=[
                    OpenApiExample("중복 리뷰 에러", value={"detail": "리뷰가 이미 존재합니다."}, response_only=True)
                ],
            ),
            401: OpenApiResponse(
                response=inline_serializer(
                    name="UnauthorizedError",
                    fields={"detail": serializers.CharField()},
                ),
                examples=[
                    OpenApiExample("인증 에러", value={"detail": "인증 토큰이 유효하지 않습니다."}, response_only=True)
                ],
            ),
        },
    )
    def post(self, request: Request, game_id: int, *args: Any, **kwargs: Any) -> Response:
        user = cast(User, request.user)

        if user.status != "active":
            return Response(
                {"detail": "비활성화된 계정입니다. 관리자에게 문의하세요."}, status=status.HTTP_400_BAD_REQUEST
            )

        serializer = GameReviewCreateSerializer(data=request.data, context={"request": request, "game_id": game_id})
        if not serializer.is_valid():
            return Response({"status": "failed", "detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        game = serializer.context["game"]
        rating = serializer.validated_data["rating"]
        content = serializer.validated_data.get("content", "")

        review = Review.objects.create(user=user, game=game, rating=rating, content=content, created_at=now())

        avg_rating = Review.objects.filter(game=game).aggregate(avg=Avg("rating"))["avg"]
        game.average_rating = round(avg_rating or 0.0, 2)
        game.save(update_fields=["average_rating"])

        response_serializer = GameReviewCreateResponseSerializer(review)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
