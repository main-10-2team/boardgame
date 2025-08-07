from typing import Any

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.exceptions import ParseError, ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.games.models import Genre
from apps.games.serializers.admin_genre_serializers import (
    AdminGenreCreateSerializer,
    AdminGenreListSerializer,
    AdminGenreUpdateSerializer,
)
from apps.users.models import User
from apps.users.utils.permission import IsAdminRole


# 관리자 장르 등록 API
@extend_schema(
    tags=["[Admin]"],
    summary="관리자 장르 등록",
    description="새로운 장르의 이름(name)을 입력받아 시스템에 등록합니다.",
    request=AdminGenreCreateSerializer,  # **[수정됨]** 시리얼라이저 이름 변경
)
class AdminGenreRegisterView(generics.CreateAPIView[Genre]):

    queryset = Genre.objects.all()
    serializer_class = AdminGenreCreateSerializer
    permission_classes = [IsAuthenticated, IsAdminRole]

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


@extend_schema(
    tags=["[Admin]"],
    summary="관리자 보드게임 장르 수정",
    description="지정된 genre_id에 해달하는 장르 레코드의 이름을 수정합니다.",
    request=AdminGenreUpdateSerializer,
)
class AdminGenreUpdateView(generics.UpdateAPIView[Genre]):
    queryset = Genre.objects.all()
    serializer_class = AdminGenreUpdateSerializer
    permission_classes = [IsAuthenticated, IsAdminRole]
    lookup_field: str = "genre_id"
    http_method_names = ["patch"]

    def patch(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        try:
            genre_id = self.kwargs.get(self.lookup_field)
            genre_instance = self.get_object()

            serializer = self.get_serializer(genre_instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)

            updated_genre_instance = serializer.save()

            response_data = {
                "id": updated_genre_instance.genre_id,
                "message": "장르 정보가 성공적으로 수정되었습니다.",
                "data": {"name": updated_genre_instance.name},
            }
            return Response(response_data, status=status.HTTP_200_OK)

        except Genre.DoesNotExist:
            return Response(
                {"error": "NOT_FOUND", "message": f"해당 ID({genre_id})의 장르를 찾을 수 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except IntegrityError:
            return Response(
                {"error": "DUPLICATE_GENRE_NAME", "message": "변경하려는 이름의 장르가 이미 존재합니다."},
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


# 관리자 장르 목록 조회 API를 위한 커스텀 페이지네이션
class GenrePagination(PageNumberPagination):

    page_size = 10
    page_size_query_param = "pageSize"
    max_page_size = 100

    def get_paginated_response(self, data: Any) -> Response:
        return Response(
            {
                "totalCount": self.page.paginator.count,  # type: ignore
                "currentPage": self.page.number,  # type: ignore
                "pageSize": self.get_page_size(self.request),  # type: ignore
                "genres": data,
            }
        )


# 관리자 장르 목록 조회
@extend_schema(
    tags=["[Admin]"],
    summary="관리자 장르 목록 조회",
    description="시스템에 등록된 모든 장르의 목록을 조회합니다. 페이징을 지원합니다.",
)
class AdminGenreListView(generics.ListAPIView[Genre]):
    queryset = Genre.objects.all().order_by("name")
    serializer_class = AdminGenreListSerializer
    permission_classes = [IsAuthenticated, IsAdminRole]
    pagination_class = GenrePagination

    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        try:
            queryset = self.filter_queryset(self.get_queryset())

            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {
                    "error": "INTERNAL_SERVER_ERROR",
                    "message": "서버에 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
