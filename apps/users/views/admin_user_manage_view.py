from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from django.http import Http404
from typing import Any

from apps.users.models import User
from apps.users.serializers.admin_user_manage_serializers import AdminUserdetailSerializer



@extend_schema(
    tags=["User - 관리자 회원 관리"],
    summary="관리자 회원 정보 조회",
    description="지정된 `user_id`에 해당하는 회원의 상세 정보를 조회합니다. 본인 또는 관리자만 접근 가능합니다.",
)
class UserInfoRetrieveView(generics.RetrieveAPIView[User]):
    queryset = User.objects.all()
    serializer_class = AdminUserdetailSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "user_id"

    # ... (기존 코드) ...

    def retrieve(self, request: Request, *args: list[Any], **kwargs: dict[str, Any]) -> Response:
        try:
            instance = self.get_object()

            # 로그인된 사용자이고, 본인 정보가 아닐 때 접근을 거부합니다.
            if request.user.is_authenticated and not request.user.is_staff and request.user.id != instance.id:  # type: ignore
                return Response(
                    {"error": "FORBIDDEN", "message": "다른 회원의 정보를 조회할 권한이 없습니다."},
                    status=status.HTTP_403_FORBIDDEN,
                )

            serializer = self.get_serializer(instance)
            return Response(serializer.data, status=status.HTTP_200_OK)

        # ... (나머지 코드) ...

        except (Http404, ValueError):
            return Response(
                {"error": "NOT_FOUND", "message": "해당 ID의 회원을 찾을 수 없습니다."},
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
