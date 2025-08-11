from http.client import responses
from typing import Any

from django.db import IntegrityError
from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.games.models import Game
from apps.games.serializers.admin_boardgame_serializers import (
    AdminGameRegisterSerializer,
)
from core.utils.permission import IsAdminRole


# 관리자 보드 게임 등록 API
@extend_schema(
    tags=["[Admin]"],
    summary="관리자 보드 게임 등록",
    description="새로운 보드 게임 정보를 시스템에 추가합니다. title은 고유해야 합니다.",
    request=AdminGameRegisterSerializer,
)
class AdminGameRegisterView(generics.CreateAPIView[Game]):

    queryset = Game.objects.all()
    serializer_class = AdminGameRegisterSerializer
    permission_classes = [IsAuthenticated, IsAdminRole]

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            game_instance = serializer.save()

            response_data = {
                "id": game_instance.game_id,
                "message": "보드 게임이 성공적으로 등록되었습니다",
                "data": serializer.data,
            }
            return Response(response_data, status=status.HTTP_200_OK)

        except ValidationError as e:
            return Response(
                {"error": "VALIDATION ERROR", "message": e.detail},
            )
        except IntegrityError:
            return Response(
                {"error": "DUPLICATE GAME", "message": "이미 동일한 이름의 보드 게임이 등록되어 있습니다"},
                status=status.HTTP_409_CONFLICT,
            )
