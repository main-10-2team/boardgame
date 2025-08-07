from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.models import User
from apps.users.serializers.auth.auth_code_email_serializers import (
    EmailSendCodeSerializer,
)
from apps.users.tasks import send_verification_email_task
from core.utils.base62 import generate_base62_code
from core.utils.redis_utils import store_restore_email_code


class ResetPasswordRequestCodeAPIView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(
        tags=["인증"],
        summary="비밀번호 재설정 인증 코드 요청",
        description="사용자가 이메일을 입력하면 인증 코드를 이메일로 전송합니다.",
        request=EmailSendCodeSerializer,
        responses={
            200: OpenApiResponse(
                description="성공",
                examples=[
                    OpenApiExample(
                        name="Success",
                        value={"status": "success", "message": "인증 코드가 이메일로 전송되었습니다."},
                    )
                ],
            ),
            400: OpenApiResponse(
                description="유효하지 않은 이메일",
                examples=[
                    OpenApiExample(
                        name="InvalidEmail",
                        value={"detail": "유효하지 않은 이메일 주소입니다."},
                    )
                ],
            ),
            404: OpenApiResponse(
                description="등록되지 않은 이메일",
                examples=[
                    OpenApiExample(
                        name="EmailNotFound",
                        value={"detail": "해당 이메일로 등록된 계정이 없습니다."},
                    )
                ],
            ),
            500: OpenApiResponse(
                description="서버 오류",
                examples=[
                    OpenApiExample(
                        name="ServerError",
                        value={"detail": "서버 오류가 발생했습니다."},
                    )
                ],
            ),
        },
    )
    def post(self, request: Request) -> Response:
        serializer = EmailSendCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        purpose = serializer.validated_data["purpose"]

        # 이메일 형식은 serializer에서 검증되었고,
        if purpose != "restore":
            return Response({"detail": "이 API는 비밀번호 재설정용입니다."}, status=400)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"detail": "해당 이메일로 등록된 계정이 없습니다."}, status=status.HTTP_404_NOT_FOUND)

        try:
            code = generate_base62_code()
            store_restore_email_code(email, code)
            send_verification_email_task.delay(email, code)
            return Response({"message": f"인증 코드{code}가 이메일로 전송되었습니다."}, status=status.HTTP_200_OK)
        except Exception:
            return Response({"detail": "서버 오류가 발생했습니다."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
