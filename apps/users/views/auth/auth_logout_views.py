from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework import permissions, status
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.serializers.auth.auth_logout_serializers import (
    LogoutResponseSerializer,
    LogoutSerializer,
)


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        request=LogoutSerializer,
        responses={
            200: OpenApiResponse(
                response=LogoutResponseSerializer,
                description="로그아웃 성공",
                examples=[
                    OpenApiExample(
                        name="성공 예시", value={"status": "success", "message": "로그아웃이 완료되었습니다."}
                    )
                ],
            ),
            400: OpenApiResponse(
                response=LogoutResponseSerializer,
                description="refresh_token 누락",
                examples=[
                    OpenApiExample(name="refresh_token 누락", value={"detail": "리프레시 토큰이 누락되었습니다."})
                ],
            ),
            401: OpenApiResponse(
                response=LogoutResponseSerializer,
                description="유효하지 않은 토큰",
                examples=[OpenApiExample(name="유효하지 않은 토큰", value={"detail": "유효하지 않은 토큰입니다."})],
            ),
            500: OpenApiResponse(
                response=LogoutResponseSerializer,
                description="서버 오류",
                examples=[OpenApiExample(name="서버 오류", value={"detail": "서버 오류가 발생했습니다."})],
            ),
        },
        tags=["인증"],
        summary="JWT 로그아웃",
        description="refresh_token을 전달받아 무효화(블랙리스트) 처리합니다.",
    )
    def post(self, request: Request) -> Response:
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        refresh_token = serializer.validated_data["refresh_token"]

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError:
            return Response({"detail": "유효하지 않은 토큰입니다."}, status=status.HTTP_401_UNAUTHORIZED)
        except Exception:
            return Response({"detail": "서버 오류가 발생했습니다."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"status": "success", "message": "로그아웃이 완료되었습니다."}, status=status.HTTP_200_OK)
