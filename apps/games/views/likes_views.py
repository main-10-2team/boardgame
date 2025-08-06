# apps/likes/views/likes_views.py

from typing import Any, cast

from django.db import transaction

# F 객체를 사용하기 위해 추가
from django.db.models import F
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.games.models import Game, Like
from apps.games.serializers.likes_serializers import (
    LikedGameSerializer,
    LikeListResponseSerializer,
    LikeResponseSerializer,
    LikeSerializer,
)
from apps.users.models import User


@extend_schema(
    tags=["좋아요"],
    summary="보드게임에 좋아요 추가/취소",
    request=LikeSerializer,
    responses={
        200: OpenApiResponse(
            response=LikeResponseSerializer,
            description="좋아요 추가/취소 성공",
            examples=[
                OpenApiExample(
                    name="좋아요 추가 성공",
                    value={
                        "status": "success",
                        "action": "added",
                        "game_id": 1,
                        "user_id": 1,
                        "total_likes": 10,
                    },
                ),
                OpenApiExample(
                    name="좋아요 취소 성공",
                    value={
                        "status": "success",
                        "action": "removed",
                        "game_id": 1,
                        "user_id": 1,
                        "total_likes": 9,
                    },
                ),
            ],
        ),
        400: OpenApiResponse(
            description="잘못된 요청",
            response=LikeSerializer,
            examples=[
                OpenApiExample(
                    name="유효하지 않은 게임 ID",
                    value={"game_id": ["유효하지 않은 게임 ID 입니다."]},
                ),
            ],
        ),
        401: OpenApiResponse(
            description="인증 실패",
            examples=[
                OpenApiExample(
                    name="인증 토큰 누락/유효하지 않음",
                    value={"detail": "인증 토큰이 유효하지 않습니다."},
                ),
            ],
        ),
    },
)
class LikeView(APIView):
    """
    특정 게임에 좋아요를 추가하거나 취소하는 API입니다.
    POST /api/v1/likes/
    """

    permission_classes = [IsAuthenticated]

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        게임에 좋아요를 추가하거나 취소합니다.
        """
        serializer = LikeSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        game_id = serializer.validated_data["game_id"]
        try:
            game = Game.objects.get(game_id=game_id)
        except Game.DoesNotExist:
            return Response({"game_id": ["유효하지 않은 게임 ID 입니다."]}, status=status.HTTP_400_BAD_REQUEST)

        user = cast(User, request.user)

        with transaction.atomic():
            try:
                like = Like.objects.get(user=user, game=game)
                like.delete()
                action = "removed"
                game.like_count -= 1
                # User 모델의 like_count 감소
                user.like_count = F("like_count") - 1
            except Like.DoesNotExist:
                Like.objects.create(user=user, game=game)
                action = "added"
                game.like_count += 1
                # User 모델의 like_count 증가
                user.like_count = F("like_count") + 1

            game.save()
            user.save()  # User 모델의 변경사항 저장

            # User 모델의 like_count를 최신 값으로 다시 불러옵니다.
            # user.refresh_from_db()  # F() 객체 사용 후 최신값 반영
            # 하지만 응답 데이터는 game.like_count만 사용하므로 굳이 필요없습니다.

            response_data = {
                "status": "success",
                "action": action,
                "game_id": game_id,
                "user_id": user.user_id,
                "total_likes": game.like_count,
            }

        return Response(response_data, status=status.HTTP_200_OK)


@extend_schema(
    tags=["좋아요"],
    summary="사용자가 좋아요 누른 게임 목록 조회",
    responses={
        200: OpenApiResponse(
            response=LikeListResponseSerializer,
            description="좋아요 누른 게임 목록 조회 성공",
            examples=[
                OpenApiExample(
                    name="성공 예시",
                    value={
                        "status": "success",
                        "user_like_count": 5,
                        "likes": [
                            {
                                "id": 101,
                                "game": {
                                    "game_id": 1,
                                    "title": "게임1",
                                    "min_players": 2,
                                    "max_players": 4,
                                    "thumbnail_url": "http://example.com/thumb1.jpg",
                                    "genres": ["전략"],
                                },
                                "created_at": "2025-08-05T09:00:00Z",
                            }
                        ],
                    },
                )
            ],
        ),
        401: OpenApiResponse(
            description="인증 실패",
            examples=[
                OpenApiExample(
                    name="인증 토큰 누락/유효하지 않음",
                    value={"detail": "인증 토큰이 유효하지 않습니다."},
                ),
            ],
        ),
        404: OpenApiResponse(
            description="좋아요한 게임 없음",
            examples=[
                OpenApiExample(
                    name="좋아요 기록 없음",
                    value={"detail": "좋아요한 게임이 없습니다."},
                ),
            ],
        ),
    },
)
class LikeListView(APIView):
    """
    현재 사용자가 좋아요를 누른 게임 목록을 조회합니다.
    GET /api/v1/likes/list/
    """

    permission_classes = [IsAuthenticated]

    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        사용자가 좋아요를 누른 게임 목록을 반환합니다.
        """
        user = cast(User, request.user)
        liked_games = Like.objects.filter(user=user).select_related("game").order_by("-created_at")

        if not liked_games.exists():
            return Response({"detail": "좋아요한 게임이 없습니다."}, status=status.HTTP_404_NOT_FOUND)

        serializer = LikedGameSerializer(liked_games, many=True)  # type: ignore
        # F() 객체를 사용했기 때문에 user 객체를 다시 불러와야 정확한 like_count를 얻을 수 있습니다.
        user_refresh = User.objects.get(pk=user.pk)
        response_data = {"status": "success", "user_like_count": user_refresh.like_count, "likes": serializer.data}

        return Response(response_data, status=status.HTTP_200_OK)
