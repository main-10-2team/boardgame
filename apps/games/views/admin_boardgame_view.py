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

from apps.games.models import Game, GameGenre
from apps.games.serializers.admin_boardgame_serializers import (
    AdminGameGenreSerializer,
    AdminGameRegisterSerializer,
    AdminGameUpdateSerializer,
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


# 관리자 보드 게임 등록


@extend_schema(
    tags=["[Admin]"],
    summary="관리자 보드 게임 수정",
    description="지정된 game_id에 해당하는 보드 게임 정보를 시스템에서 부분적으로 또는 전체적으로 수정합니다.",
    request=AdminGameUpdateSerializer,
)
class AdminGameUpdateView(generics.UpdateAPIView[Game]):
    queryset = Game.objects.all()
    serializer_class = AdminGameUpdateSerializer
    permission_classes = [IsAuthenticated, IsAdminRole]
    lookup_field: str = "game_id"
    http_method_names = ["patch"]

    def patch(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        try:
            # game_id에 해당하는 게임 인스턴스를 가져옵니다.
            game_id = self.kwargs.get(self.lookup_field)
            instance = self.get_object()

            serializer = self.get_serializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)

            updated_game_instance = serializer.save()

            response_data = {
                "id": updated_game_instance.game_id,
                "message": "보드 게임 정보가 성공적으로 수정되었습니다.",
                "data": serializer.data,
            }
            return Response(response_data, status=status.HTTP_200_OK)

        except Game.DoesNotExist:
            return Response(
                {"error": "NOT_FOUND", "message": f"해당 ID({game_id})의 보드 게임을 찾을 수 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )
        # 타이틀 중복 등으로 인한 DB 무결성 오류
        except IntegrityError:
            return Response(
                {"error": "DUPLICATE_GAME_NAME", "message": "입력된 게임 이름이 이미 존재합니다."},
                status=status.HTTP_409_CONFLICT,
            )
        # 시리얼라이저 유효성 검사 오류 (min_players > max_players 등)
        except ValidationError as e:
            return Response({"error": "VALIDATION_ERROR", "message": e.detail}, status=status.HTTP_400_BAD_REQUEST)


# 관리자 게임-장르 관계 생성
@extend_schema(
    tags=["[Admin]"],
    summary="관리자 게임-장르 연결",
    description="특정 게임에 장르를 연결합니다. 이미 연결된 경우 충돌 오류를 반환합니다.",
    request=AdminGameGenreSerializer,
)
class AdminGameGenreCreateView(generics.CreateAPIView[GameGenre]):
    queryset = GameGenre.objects.all()
    serializer_class = AdminGameGenreSerializer
    permission_classes = [IsAuthenticated, IsAdminRole]

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            game_genre_instance = serializer.save()

            response_data = {
                "id": game_genre_instance.id,
                "game_id": game_genre_instance.game.game_id,
                "genre_id": game_genre_instance.genre.genre_id,
                "game_title": game_genre_instance.game.title,
                "genre_name": game_genre_instance.genre.name,
                "created_at": game_genre_instance.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            }
            return Response(response_data, status=status.HTTP_201_CREATED)

        except ValidationError as e:
            if "해당 게임과 장르는 이미 연결되어 있습니다." in str(e.detail):
                return Response(
                    {"error": "DUPLICATE_RELATION", "message": "해당 게임과 장르는 이미 연결되어 있습니다."},
                    status=status.HTTP_409_CONFLICT,
                )
            return Response({"error": "VALIDATION_ERROR", "message": e.detail}, status=status.HTTP_400_BAD_REQUEST)


# 관리자 게임-장르 관계 삭제
@extend_schema(
    tags=["[Admin] Game-Genre - 관리자 게임-장르 연결 관리"],
    summary="관리자 게임-장르 연결 해제",
    description="특정 게임-장르 관계 ID를 통해 연결을 해제합니다.",
)
class AdminGameGenreDeleteView(generics.DestroyAPIView[GameGenre]):
    queryset = GameGenre.objects.all()
    permission_classes = [IsAuthenticated, IsAdminRole]
    lookup_field: str = "pk"

    def delete(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        try:
            game_genre_id = self.kwargs.get(self.lookup_field)
            instance = self.get_object()

            instance.delete()

            return Response(status=status.HTTP_204_NO_CONTENT)

        except GameGenre.DoesNotExist:
            return Response(
                {"error": "NOT_FOUND", "message": f"해당 ID({game_genre_id})의 게임-장르 관계를 찾을 수 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )
