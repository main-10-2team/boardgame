# apps/likes/views/likes_remove_views.py

from typing import Any, cast

from django.db import transaction

# F 객체를 사용하기 위해 import 추가
from django.db.models import F
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.games.models import Game, Like
from apps.games.serializers.likes_serializers import LikeSerializer
from apps.users.models import User


@extend_schema(
    tags=["좋아요"],
    summary="좋아요 제거 (목록에서 제거)",
    description="사용자가 좋아요 누른 게임 목록에서 특정 게임을 제거합니다.",
    request=LikeSerializer,
    responses={
        200: OpenApiResponse(
            description="좋아요 제거 성공",
            examples=[
                OpenApiExample(
                    name="성공 예시",
                    value={
                        "status": "success",
                        "message": "좋아요가 취소되었습니다.",
                        "game_id": 123,
                        "heart_icon_active": False,
                        "total_likes": 41,
                    },
                ),
            ],
        ),
        400: OpenApiResponse(
            description="잘못된 요청",
            examples=[
                OpenApiExample(
                    name="좋아요가 존재하지 않음",
                    value={"detail": "좋아요가 존재하지 않습니다."},
                ),
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
                    name="유효하지 않은 토큰",
                    value={"detail": "인증 토큰이 유효하지 않습니다."},
                ),
            ],
        ),
    },
)
class LikeRemoveView(APIView):
    """
    특정 게임에 대한 좋아요를 삭제하는 API입니다.
    POST /api/v1/likes/remove/
    """

    permission_classes = [IsAuthenticated]

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = LikeSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        game_id = serializer.validated_data["game_id"]
        user = cast(User, request.user)

        with transaction.atomic():
            try:
                like_to_delete = Like.objects.get(user=user, game_id=game_id)
                like_to_delete.delete()

                game = Game.objects.get(game_id=game_id)
                game.like_count = F("like_count") - 1
                game.save()
                game.refresh_from_db()  # <-- 여기!

                user.like_count = F("like_count") - 1
                user.save()
                # user.refresh_from_db() # user.like_count를 응답에 포함한다면 이 라인도 필요

                response_data = {
                    "status": "success",
                    "message": "좋아요가 취소되었습니다.",
                    "game_id": game_id,
                    "heart_icon_active": False,
                    "total_likes": game.like_count,
                }
                return Response(response_data, status=status.HTTP_200_OK)

            except Like.DoesNotExist:
                return Response({"detail": "좋아요가 존재하지 않습니다."}, status=status.HTTP_400_BAD_REQUEST)

            except Game.DoesNotExist:
                return Response({"game_id": ["유효하지 않은 게임 ID 입니다."]}, status=status.HTTP_400_BAD_REQUEST)
