from typing import Any

from django.http import Http404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.models import User
from apps.users.serializers.admin_user_manage_serializers import (
    AdminUserdetailSerializer,
    UserDeactivateSerializer,
    UserSuspendSerializer,
)


@extend_schema(
    tags=["[Admin]"],
    summary="관리자 회원 정보 조회",
    description="지정된 `user_id`에 해당하는 회원의 상세 정보를 조회합니다. 본인 또는 관리자만 접근 가능합니다.",
)
class AdminUserDetailView(generics.RetrieveAPIView[User]):
    queryset = User.objects.all()
    serializer_class = AdminUserdetailSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "user_id"

    def retrieve(self, request: Request, *args: list[Any], **kwargs: dict[str, Any]) -> Response:
        try:
            instance = self.get_object()

            # 관리자가 아닐 때 오류 메시지
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


class IsAdminRole(IsAdminUser):
    def has_permission(self, request: Request, view: APIView) -> bool:
        # request.user가 None이거나 인증되지 않았다면 False를 반환합니다.
        if not request.user or not request.user.is_authenticated:
            return False

        # 'role' 필드는 User 모델에 명시적으로 정의되어 있으므로 hasattr 검사는 필요하지 않습니다.
        return request.user.role == "admin"


@extend_schema(
    tags=["[Admin]"],
    summary="관리자 회원 제재 (활동 정지)",
    description="특정 회원의 활동을 일시적 또는 영구적으로 정지시킵니다. 제재 기간 정보는 User 모델의 suspended_until 필드에 저장됩니다.",
    request=UserSuspendSerializer,
)
# 회원 제재 (활동 정지) API
class AdminUserSuspendView(generics.UpdateAPIView[User]):
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = UserSuspendSerializer
    lookup_field = "user_id"

    def patch(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        try:
            user_id = self.kwargs.get(self.lookup_field)
            user = self.get_object()  # user_id에 해당하는 User 객체 가져오기 (없으면 404 발생)

            if user == request.user:
                raise ValidationError("자기 자신을 제재할 수 없습니다.")

            if user.status == "deleted":
                raise ValidationError("이미 탈퇴된 회원은 제재할 수 없습니다.")

            serializer = self.get_serializer(user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)

            # 시리얼라이저의 update 메서드를 호출하여 로직 위임
            serializer.save()

            # 응답 메시지 구성 (duration은 serializer.validated_data에서 가져옴)
            duration = serializer.validated_data.get("duration")
            message_duration = ""
            if duration is not None and duration > 0:
                message_duration = f"가 {duration}일간 정지되었습니다."
            else:
                message_duration = "가 영구 정지되었습니다."

            return Response(
                {"message": f"회원 {user_id}{message_duration}", "user_id": user_id, "status": "SUSPENDED"},
                status=status.HTTP_200_OK,
            )
        except User.DoesNotExist:
            return Response(
                {"error": "NOT_FOUND", "message": f"해당 ID({user_id})의 회원을 찾을 수 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
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
    summary="관리자 회원 탈퇴 (영구 삭제)",
    description="특정 회원의 계정을 시스템에서 영구적으로 삭제합니다.",
    request=UserDeactivateSerializer,
)
# 회원 탈퇴 (영구 삭제) API
class AdminUserDeactivateView(generics.UpdateAPIView[User]):
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = UserDeactivateSerializer
    lookup_field = "user_id"

    def patch(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        try:
            user_id = self.kwargs.get(self.lookup_field)
            user = self.get_object()

            if user == request.user:
                raise ValidationError("자기 자신을 탈퇴 처리할 수 없습니다.")

            if user.status == "deleted":
                raise ValidationError("이미 탈퇴된 회원입니다.")

            serializer = self.get_serializer(user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)

            # 시리얼라이저의 update 메서드를 호출하여 로직 위임
            updated_user = serializer.save()

            message = ""
            if updated_user is None:  # 시리얼라이저에서 user.delete()가 호출된 경우
                message = f"회원 {user_id}가 모든 관련 데이터와 함께 성공적으로 탈퇴 처리되었습니다."
            else:
                message = f"회원 {user_id}가 성공적으로 탈퇴 처리되었습니다."

            return Response(
                {"message": message, "user_id": user_id, "status": "DEACTIVATED"}, status=status.HTTP_200_OK
            )

        except User.DoesNotExist:
            return Response(
                {"error": "NOT_FOUND", "message": f"해당 ID({user_id})의 회원을 찾을 수 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
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
