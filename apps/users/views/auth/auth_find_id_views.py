# apps/users/views/auth/auth_find_id_views.py
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.models import User
from apps.users.serializers.auth.auth_find_id_serializers import (
    FindIDRequestSerializer,
    FindIDResponseSerializer,
)


class FindIDAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    @extend_schema(
        request=FindIDRequestSerializer,
        responses={
            200: OpenApiResponse(
                response=FindIDResponseSerializer,
                description="아이디 조회 성공",
                examples=[
                    OpenApiExample(
                        name="아이디 조회 성공",
                        value={
                            "status": "success",
                            "message": "아이디 조회가 완료되었습니다.",
                            "email": "user@example.com",
                        },
                    )
                ],
            ),
            400: OpenApiResponse(
                description="유효하지 않은 휴대전화 번호",
                examples=[
                    OpenApiExample(
                        name="400 에러 - 휴대전화 유효성 실패", value={"detail": "유효하지 않은 휴대전화 번호입니다."}
                    )
                ],
            ),
            404: OpenApiResponse(
                description="해당 번호로 등록된 계정 없음",
                examples=[
                    OpenApiExample(
                        name="404 에러 - 계정 없음", value={"detail": "해당 휴대전화 번호로 등록된 계정이 없습니다."}
                    )
                ],
            ),
            500: OpenApiResponse(
                description="서버 오류",
                examples=[OpenApiExample(name="500 에러 - 서버 오류", value={"detail": "서버 오류가 발생했습니다."})],
            ),
        },
        tags=["인증"],
        summary="아이디(이메일) 찾기 API",
        description="휴대전화 번호로 가입된 사용자의 이메일 주소를 조회하는 API입니다. 형식 +821012345678",
    )
    def post(self, request: Request) -> Response:
        serializer = FindIDRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"detail": "유효하지 않은 휴대전화 번호입니다."}, status=status.HTTP_400_BAD_REQUEST)

        phone_number = serializer.validated_data["phone_number"]

        try:
            user = User.objects.get(phone_number=phone_number)
        except User.DoesNotExist:
            return Response(
                {"detail": "해당 휴대전화 번호로 등록된 계정이 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception:
            return Response(
                {"detail": "서버 오류가 발생했습니다."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {
                "status": "success",
                "message": "아이디 조회가 완료되었습니다.",
                "email": user.email,
            },
            status=status.HTTP_200_OK,
        )
