from typing import Any

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.exceptions import ParseError, ValidationError
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.games.models import Genre
from apps.games.serializers.admin_genre_serializers import AdminGenreCreateSerializer

User = get_user_model()


class IsAdminRole(IsAdminUser):

    def has_permission(self, request: Request, view: APIView) -> bool:
        return bool(request.user and request.user.is_authenticated and request.user.role == "admin")


# 관리자 장르 등록 API


@extend_schema(
    tags=["[Admin] Genre - 관리자 장르 관리"],
    summary="관리자 장르 등록",
    description="새로운 장르의 이름(name)을 입력받아 시스템에 등록합니다.",
    request=AdminGenreCreateSerializer,  # **[수정됨]** 시리얼라이저 이름 변경
)
class AdminGenreRegisterView(generics.CreateAPIView[Genre]):

    queryset = Genre.objects.all()
    serializer_class = AdminGenreCreateSerializer
    permission_classes = [AllowAny]

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            genre_instance = serializer.save()

            response_data = {
                "id": genre_instance.genre_id,
                "message": "장르가 성공적으로 등록되었습니다.",
                "data": {"name": genre_instance.name},
            }
            return Response(response_data, status=status.HTTP_201_CREATED)

        except IntegrityError:
            return Response(
                {"error": "DUPLICATE_GENRE_NAME", "message": "이미 동일한 이름의 장르가 존재합니다."},
                status=status.HTTP_409_CONFLICT,
            )
        except ValidationError as e:
            return Response({"error": "VALIDATION_ERROR", "message": e.detail}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {
                    "error": "INTERNAL_SERVER_ERROR",
                    "message": "서버에 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
