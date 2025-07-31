import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import redis
from django.contrib.auth import login
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.models import User
from apps.users.serializers.auth_code_email_serializers import (
    EmailSendCodeSerializer,
    EmailVerifyCodeSerializer,
)
from apps.users.serializers.auth_signup_serializers import SignupSerializer
from apps.users.tasks import send_verification_email_task
from apps.users.utils.base62 import generate_base62_code
from apps.users.utils.redis_utils import (
    delete_restore_email_code,
    delete_signup_email_code,
    get_restore_email_code,
    get_signup_email_code,
    mark_restore_email_as_verified,
    mark_signup_email_as_verified,
    store_restore_email_code,
    store_signup_email_code,
)

logger = logging.getLogger(__name__)


class SendEmailCodeView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(
        request=EmailSendCodeSerializer, responses={200: None}, summary="이메일 인증 코드 전송", tags=["인증"]
    )
    def post(self, request: Request) -> Response:
        serializer = EmailSendCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email: str = serializer.validated_data["email"]
        code: str = generate_base62_code()
        purpose: str = serializer.validated_data["purpose"]

        if purpose == "signup":
            store_signup_email_code(email, code)
        elif purpose == "restore":
            store_restore_email_code(email, code)

        send_verification_email_task.delay(email, code)

        return Response({"message": "인증 코드가 이메일로 전송되었습니다."}, status=status.HTTP_200_OK)


class VerifyEmailCodeView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(
        request=EmailVerifyCodeSerializer,
        responses={200: None, 400: None},
        summary="이메일 인증코드 검증",
        tags=["인증"],
    )
    def post(self, request: Request) -> Response:
        serializer = EmailVerifyCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        input_code = serializer.validated_data["verification_code"]
        purpose = serializer.validated_data["purpose"]

        if purpose == "signup":
            stored_code = get_signup_email_code(email)
            if stored_code is None:
                return Response({"error": "인증 코드가 만료되었거나 존재하지 않습니다."}, status=410)
            if stored_code != input_code:
                return Response({"error": "인증 코드가 일치하지 않습니다."}, status=401)
            delete_signup_email_code(email)
            mark_signup_email_as_verified(email)

        elif purpose == "restore":
            stored_code = get_restore_email_code(email)
            if stored_code is None:
                return Response({"error": "인증 코드가 만료되었거나 존재하지 않습니다."}, status=410)
            if stored_code != input_code:
                return Response({"error": "인증 코드가 일치하지 않습니다."}, status=401)
            delete_restore_email_code(email)
            mark_restore_email_as_verified(email)

        return Response({"message": "이메일 인증이 완료되었습니다."}, status=status.HTTP_200_OK)


class SignupView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        tags=["인증"],
        summary="이메일 회원 가입",
        operation_id="signup",
        description="이메일 인증번호를 포함하여 새로운 사용자를 등록합니다. 성공 시 사용자 정보와 JWT 토큰을 반환합니다.",
        request=SignupSerializer,  # SignupSerializer에 email_verification_code가 포함됨
        examples=[
            OpenApiExample(
                "회원가입 요청 예시",
                value={
                    "email": "user@example.com",
                    "password": "SecurePass123!",
                    "nickname": "GameLover",
                    "phone_number": "+821012345678",
                    "birth": "1990-01-01",
                    "profile_img_file": "binary",
                    "email_verification_code": "123456",  # 다시 포함
                    "preferred_genres": [1, 2],
                    "preferred_playtime": [3, 4],
                },
                request_only=True,
                media_type="multipart/form-data",
            ),
            OpenApiExample(
                "회원가입 성공 응답 예시",
                value={
                    "status": "success",
                    "message": "회원가입이 완료되었습니다.",
                    "user": {
                        "user_id": 1,
                        "email": "user@example.com",
                        "nickname": "GameLover",
                        "phone_number": "+821012345678",
                        "birth": "1990-01-01T00:00:00Z",
                        "role": "user",
                        "status": "active",
                        "created_at": "2025-07-29T14:42:00Z",
                        "updated_at": "2025-07-29T14:42:00Z",
                    },
                    "profile_img_url": "https://storage.example.com/profile/asdd.png",
                    "preferred_genres": ["Strategy", "Family"],
                    "preferred_playtime": ["30-60min", "60-90min"],
                    "access_token": "...",
                    "refresh_token": "...",
                },
                response_only=True,
                status_codes=["200"],
            ),
        ],
        responses={
            200: SignupSerializer,
            400: OpenApiResponse(
                description="Bad Request",
                examples=[
                    OpenApiExample(
                        "유효성 검사 실패 예시 (일반 필드)",
                        value={"detail": {"email": ["이미 등록된 이메일입니다."]}},
                        media_type="application/json",
                    ),
                    OpenApiExample(
                        "유효성 검사 실패 예시 (인증 코드)",
                        value={"detail": {"email_verification_code": ["인증 코드가 만료되었거나 유효하지 않습니다."]}},
                        media_type="application/json",
                    ),
                ],
            ),
            500: OpenApiResponse(
                description="Internal Server Error",
                examples=[
                    OpenApiExample("서버 오류 예시", value={"detail": "server_error"}, media_type="application/json")
                ],
            ),
        },
    )
    def post(self, request: Request) -> Response:
        serializer = SignupSerializer(data=request.data)
        if not serializer.is_valid():
            # 시리얼라이저의 validate 메서드에서 인증 코드 검증 실패 시
            # 해당 에러가 serializer.errors에 포함되어 반환됩니다.
            return Response({"detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        # 사용자 생성
        try:
            user: User = serializer.save()

            login(request, user, backend="django.contrib.auth.backends.ModelBackend")  # type: ignore
            refresh = RefreshToken.for_user(user)

            preferred_playtime_names = [pt.playtime_category.name for pt in user.user_preferred_playtimes.all()]

            response_data = {
                "status": "success",
                "message": "회원가입이 완료되었습니다.",
                "user": {
                    "user_id": user.user_id,
                    "email": user.email,
                    "nickname": user.nickname,
                    "phone_number": user.phone_number,
                    "birth": user.birth.isoformat(),
                    "role": user.role,
                    "status": user.status,
                    "created_at": user.created_at.isoformat(),
                    "updated_at": user.updated_at.isoformat(),
                },
                "profile_img_url": user.profile_image if user.profile_image else None,
                "preferred_genres": [genre.genre.name for genre in user.user_preferred_genres.all()],
                "preferred_playtime": preferred_playtime_names,
                "access_token": str(refresh.access_token),
                "refresh_token": str(refresh),
            }
            response = Response(response_data, status=status.HTTP_200_OK)
            response.set_cookie("refresh_token", str(refresh), httponly=True, secure=True, max_age=7 * 24 * 60 * 60)
            return response
        except Exception as e:
            logger.exception("회원가입 중 서버 오류 발생: %s", str(e))
            return Response({"detail": "server_error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
