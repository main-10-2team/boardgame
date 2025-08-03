import logging
from typing import cast

from typing import Any

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.models import User
from apps.users.serializers.profile_serializers import (
    UserProfileSerializer,
    UserProfileUpdateSerializer,
    PasswordChangeSerializer,
)


@extend_schema(
    summary="유저 프로필 조회",
    description="로그인한 사용자의 프로필 정보를 조회합니다.",
    tags=["유저"],
    responses={
        200: UserProfileSerializer,
        401: OpenApiResponse(
            description="인증 실패. 유효하지 않거나 누락된 토큰",
            response={
                "type": "object",
                "properties": {"detail": {"type": "string", "example": "자격 인증 헤더가 제공되지 않았습니다."}},
                "required": ["detail"],
            },
        ),
        500: OpenApiResponse(
            description="서버 내부 오류",
            response={
                "type": "object",
                "properties": {
                    "detail": {"type": "string", "example": "서버 오류가 발생했습니다. 나중에 다시 시도해 주세요."}
                },
                "required": ["detail"],
            },
        ),
    },
)
class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        user = cast(User, request.user)

        serializer = UserProfileSerializer(user)
        return Response(serializer.data)


logger = logging.getLogger(__name__)


@extend_schema(
    summary="유저 프로필 수정",
    description="로그인한 사용자가 자신의 프로필 정보를 수정합니다. 비밀번호 검증 및 닉네임 중복 확인을 수행합니다.",
    tags=["유저"],
    request={"multipart/form-data": UserProfileUpdateSerializer},
    responses={
        200: OpenApiResponse(
            description="수정 성공",
            response=UserProfileSerializer,
        ),
        400: OpenApiResponse(
            description="입력 데이터 오류 또는 비밀번호 불일치, 닉네임 중복",
            response={
                "type": "object",
                "properties": {
                    "nickname": {"type": "array", "items": {"type": "string"}},
                    "phone_number": {"type": "array", "items": {"type": "string"}},
                    "password": {"type": "array", "items": {"type": "string"}},
                },
            },
        ),
        401: OpenApiResponse(
            description="인증 실패",
            response={
                "type": "object",
                "properties": {"detail": {"type": "string", "example": "자격 인증 헤더가 제공되지 않았습니다."}},
            },
        ),
        500: OpenApiResponse(
            description="서버 내부 오류",
            response={
                "type": "object",
                "properties": {
                    "detail": {"type": "string", "example": "서버 오류가 발생했습니다. 나중에 다시 시도해 주세요."}
                },
                "required": ["detail"],
            },
        ),
    },
)
class UserProfileUpdateView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def patch(self, request: Request) -> Response:
        try:
            user = cast(User, request.user)

            serializer = UserProfileUpdateSerializer(
                instance=user,
                data=request.data,
                partial=True,
                context={"request": request},
            )
            if serializer.is_valid():
                serializer.save()
                return Response(
                    {
                        "message": "프로필이 성공적으로 수정되었습니다.",
                        "user": UserProfileSerializer(user).data,
                    }
                )

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.exception("유저 프로필 수정 중 오류 발생")
            return Response(
                {"detail": "서버 오류가 발생했습니다. 나중에 다시 시도해 주세요."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@extend_schema(
    summary="비밀번호 변경",
    description="로그인한 사용자가 현재 비밀번호를 검증한 후 새 비밀번호로 변경합니다.",
    tags=["유저"],
    request=PasswordChangeSerializer,
    responses={
        200: OpenApiResponse(
            description="비밀번호 변경 성공",
            response={
                "type": "object",
                "properties": {"message": {"type": "string", "example": "비밀번호가 성공적으로 변경되었습니다."}},
                "required": ["message"],
            },
        ),
        400: OpenApiResponse(
            description="유효성 검증 실패 또는 입력 오류",
            response={
                "type": "object",
                "properties": {
                    "current_password": {
                        "type": "array",
                        "items": {"type": "string"},
                        "example": ["현재 비밀번호가 일치하지 않습니다."],
                    },
                    "new_password": {
                        "type": "array",
                        "items": {"type": "string"},
                        "example": ["비밀번호는 8자 이상이어야 합니다."],
                    },
                    "new_password_confirm": {
                        "type": "array",
                        "items": {"type": "string"},
                        "example": ["비밀번호가 서로 일치하지 않습니다."],
                    },
                },
            },
        ),
        401: OpenApiResponse(
            description="인증 실패 - 유효하지 않거나 누락된 토큰",
            response={
                "type": "object",
                "properties": {"detail": {"type": "string", "example": "자격 인증 헤더가 제공되지 않았습니다."}},
                "required": ["detail"],
            },
        ),
        500: OpenApiResponse(
            description="서버 내부 오류",
            response={
                "type": "object",
                "properties": {
                    "detail": {"type": "string", "example": "서버 오류가 발생했습니다. 나중에 다시 시도해 주세요."}
                },
                "required": ["detail"],
            },
        ),
    },
)
class PasswordChangeView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = PasswordChangeSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "비밀번호가 성공적으로 변경되었습니다."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
