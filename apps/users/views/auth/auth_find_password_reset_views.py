# apps/users/views/auth/auth_find_password_reset_views.py

from django.contrib.auth.hashers import make_password
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.serializers.auth.auth_find_password_reset_serializers import (
    PasswordResetVerifySerializer,
)
from apps.users.utils.redis_utils import delete_restore_email_code


class PasswordResetVerifyAPIView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(
        request=PasswordResetVerifySerializer,
        responses={
            200: {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "example": "success"},
                    "message": {"type": "string", "example": "비밀번호가 성공적으로 재설정되었습니다."},
                },
            },
            400: {
                "type": "object",
                "properties": {"detail": {"type": "string", "example": "유효하지 않은 인증 코드입니다."}},
            },
            403: {
                "type": "object",
                "properties": {"detail": {"type": "string", "example": "계정이 비활성화되었습니다."}},
            },
            404: {
                "type": "object",
                "properties": {"detail": {"type": "string", "example": "해당 이메일로 등록된 계정이 없습니다."}},
            },
        },
        summary="비밀번호 재설정",
        tags=["인증"],
    )
    def post(self, request: Request) -> Response:
        serializer = PasswordResetVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]
        new_password = serializer.validated_data["new_password"]

        user.password = make_password(new_password)
        user.save()

        delete_restore_email_code(user.email)

        return Response(
            {"status": "success", "message": "비밀번호가 성공적으로 재설정되었습니다."}, status=status.HTTP_200_OK
        )
