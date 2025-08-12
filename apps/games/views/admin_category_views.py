from typing import Any, Optional

from django.db import IntegrityError
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from apps.games.models import Category, GameCategory
from apps.games.serializers.admin_category_serializers import (
    AdminCategoryCreateSerializer,
    AdminCategoryListSerializer,
    AdminCategoryUpdateSerializer,
)
from core.utils.permission import IsAdminRole


# 관리자 카테고리 등록 API View (POST)
@extend_schema(
    tags=["[Admin]"],
    summary="관리자 카테고리 등록",
    description="새로운 보드 게임 카테고리 정보를 시스템에 추가합니다. name은 고유해야 합니다.",
    request=AdminCategoryCreateSerializer,
)
class AdminCategoryCreateView(generics.CreateAPIView[Category]):
    queryset = Category.objects.all()
    serializer_class = AdminCategoryCreateSerializer
    permission_classes = [IsAuthenticated, IsAdminRole]

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            category_instance = serializer.save()

            response_data = {
                "id": category_instance.category_id,
                "message": "카테고리가 성공적으로 등록되었습니다.",
                "data": serializer.data,
            }
            return Response(response_data, status=status.HTTP_201_CREATED)

        except IntegrityError:
            return Response(
                {"error": "DUPLICATE_CATEGORY_NAME", "message": "이미 동일한 이름의 카테고리가 등록되어 있습니다."},
                status=status.HTTP_409_CONFLICT,
            )
        except ValidationError as e:
            return Response({"error": "VALIDATION_ERROR", "message": e.detail}, status=status.HTTP_400_BAD_REQUEST)


# 관리자 카테고리 목록 조회 API View (GET)
@extend_schema(
    tags=["[Admin]"],
    summary="관리자 카테고리 목록 조회",
    description="시스템에 등록된 모든 카테고리 목록을 조회합니다.",
    request=AdminCategoryListSerializer,
)
class AdminCategoryListView(generics.ListAPIView[Category]):
    queryset = Category.objects.all()
    serializer_class = AdminCategoryListSerializer
    permission_classes = [IsAuthenticated, IsAdminRole]

    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        try:
            queryset = self.filter_queryset(self.get_queryset())
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


# 관리자 카테고리 수정 API View (PATCH)
@extend_schema(
    tags=["[Admin]"],
    summary="관리자 카테고리 수정",
    description="지정된 category_id에 해당하는 카테고리 정보를 수정합니다. name은 고유해야 합니다.",
    request=AdminCategoryUpdateSerializer,
)
class AdminCategoryUpdateView(generics.UpdateAPIView[Category]):
    queryset = Category.objects.all()
    serializer_class = AdminCategoryUpdateSerializer
    permission_classes = [IsAuthenticated, IsAdminRole]
    lookup_field: str = "category_id"
    http_method_names = ["patch"]

    def patch(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        try:
            category_id = self.kwargs.get(self.lookup_field)
            instance = self.get_object()

            serializer = self.get_serializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)

            updated_category_instance = serializer.save()

            response_data = {
                "id": updated_category_instance.category_id,
                "message": "카테고리 정보가 성공적으로 수정되었습니다.",
                "data": serializer.data,
            }
            return Response(response_data, status=status.HTTP_200_OK)

        except Category.DoesNotExist:
            return Response(
                {"error": "NOT_FOUND", "message": f"해당 ID({category_id})의 카테고리를 찾을 수 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except IntegrityError:
            return Response(
                {"error": "DUPLICATE_CATEGORY_NAME", "message": "이미 동일한 이름의 카테고리가 등록되어 있습니다."},
                status=status.HTTP_409_CONFLICT,
            )
        except ValidationError as e:
            return Response({"error": "VALIDATION_ERROR", "message": e.detail}, status=status.HTTP_400_BAD_REQUEST)


# 관리자 카테고리 삭제 API View (DELETE)
@extend_schema(
    tags=["[Admin]"],
    summary="관리자 카테고리 삭제",
    description="지정된 category_id에 해당하는 카테고리를 시스템에서 삭제합니다. 해당 카테고리가 게임과 연결되어 있다면 409 Conflict를 반환합니다.",
)
class AdminCategoryDeleteView(generics.DestroyAPIView[Category]):
    queryset = Category.objects.all()
    permission_classes = [IsAuthenticated, IsAdminRole]
    lookup_field: str = "category_id"

    def delete(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        try:
            category_id_raw: Optional[int] = self.kwargs.get(self.lookup_field)
            if category_id_raw is None:
                raise NotFound("카테고리 ID가 제공되지 않았습니다.")

            category_id = int(category_id_raw)

            instance = self.get_object()

            # 해당 카테고리를 사용하는 게임이 있는지 확인
            if GameCategory.objects.filter(category=instance).exists():
                return Response(
                    {
                        "error": "CATEGORY_IN_USE",
                        "message": "해당 카테고리를 사용하는 보드 게임이 존재하여 삭제할 수 없습니다.",
                    },
                    status=status.HTTP_409_CONFLICT,
                )

            instance.delete()

            return Response(
                {"id": category_id, "message": "카테고리가 성공적으로 삭제되었습니다."}, status=status.HTTP_200_OK
            )

        except Category.DoesNotExist:
            return Response(
                {"error": "NOT_FOUND", "message": f"해당 ID({category_id_raw})의 카테고리를 찾을 수 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            return Response(
                {
                    "error": "INTERNAL_SERVER_ERROR",
                    "message": "서버에 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
