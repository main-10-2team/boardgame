from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.models import User
from apps.users.serializers.profile_serializers import UserProfileSerializer


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
        assert isinstance(request.user, User)

        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)
