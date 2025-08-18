# apps/users/views/auth/auth_find_password_reset_views.py

from django.contrib.auth.hashers import make_password
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.serializers.auth.auth_find_password_reset_serializers import (
    PasswordResetSetPasswordSerializer,
    PasswordResetVerifyCodeSerializer,
)
from core.utils.redis_utils import delete_reset_email_token  # 수정: 토큰 삭제 함수 사용


# 비밀번호 재설정 - 인증 코드 검증 API (토큰 발급)
class PasswordResetVerifyCodeAPIView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(
        request=PasswordResetVerifyCodeSerializer,
        responses={200: {"properties": {"message": {"type": "string"}, "reset_token": {"type": "string"}}}, 400: None},
        summary="비밀번호 재설정용 이메일 인증코드 검증 및 토큰 발급",
        tags=["인증"],
    )
    def post(self, request: Request) -> Response:
        serializer = PasswordResetVerifyCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data["token"]
        return Response({"message": "인증 코드가 확인되었습니다.", "reset_token": token}, status=status.HTTP_200_OK)


# 비밀번호 재설정 - 새 비밀번호 설정 API (토큰 기반)
class PasswordResetSetPasswordAPIView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(
        request=PasswordResetSetPasswordSerializer,
        responses={
            200: {"description": "비밀번호가 성공적으로 재설정되었습니다."},
            400: {"description": "요청 데이터가 유효하지 않습니다."},
        },
        summary="비밀번호 재설정 (토큰 기반)",
        tags=["인증"],
    )
    def post(self, request: Request) -> Response:
        serializer = PasswordResetSetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]
        new_password = serializer.validated_data["new_password"]
        token = serializer.validated_data["reset_token"]

        user.password = make_password(new_password)
        user.save()

        # 비밀번호 재설정 성공 후, 사용된 토큰 삭제
        delete_reset_email_token(token)

        return Response(
            {"status": "success", "message": "비밀번호가 성공적으로 재설정되었습니다."},
            status=status.HTTP_200_OK,
        )
