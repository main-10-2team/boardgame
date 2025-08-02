from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.models import User
from apps.users.serializers.auth.auth_email_login_serializers import (
    EmailLoginResponseSerializer,
    EmailLoginSerializer,
)


class EmailLoginAPIView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=EmailLoginSerializer,
        responses={
            200: OpenApiResponse(
                response=EmailLoginResponseSerializer,
                description="로그인 성공",
                examples=[
                    OpenApiExample(
                        name="로그인 성공",
                        value={
                            "message": "이메일 로그인에 성공했습니다.",
                            "access_token": "access.jwt.token",
                            "refresh_token": "refresh.jwt.token",
                            "user": {
                                "user_id": 1,
                                "email": "test@example.com",
                                "nickname": "tester",
                                "phone_number": "+821012345678",
                                "birth": "1970-01-01",
                                "role": "admin",
                                "status": 1,
                            },
                        },
                    )
                ],
            ),
            401: OpenApiResponse(
                response=EmailLoginResponseSerializer,
                description="잘못된 자격 정보",
                examples=[
                    OpenApiExample(name="401 에러", value={"detail": "이메일 또는 비밀번호가 올바르지 않습니다."})
                ],
            ),
            403: OpenApiResponse(
                response=EmailLoginResponseSerializer,
                description="비활성화된 계정",
                examples=[OpenApiExample(name="403 에러", value={"detail": "탈퇴한 계정입니다."})],
            ),
            400: OpenApiResponse(
                response=EmailLoginResponseSerializer,
                description="입력값 검증 실패",
                examples=[
                    OpenApiExample(
                        name="400 에러",
                        value={"email": ["이 필드는 필수 항목입니다."], "password": ["이 필드는 필수 항목입니다."]},
                    )
                ],
            ),
        },
        tags=["인증"],
        summary="이메일 로그인",
    )
    def post(self, request: Request) -> Response:
        print("📥 요청 데이터:", request.data)

        serializer = EmailLoginSerializer(data=request.data)
        print("🧾 serializer.is_valid() 호출 전")

        if serializer.is_valid():
            print("✅ serializer.is_valid() = True")
            email = serializer.validated_data["email"]
            password = serializer.validated_data["password"]

            try:
                user = User.objects.get(email=email)
                print(f"👤 유저 조회 성공: {user.email}, 활성화 여부: {user.is_active}")

                if not user.is_active:
                    print("❌ 비활성화된 계정")
                    return Response({"detail": "탈퇴한 계정입니다."}, status=403)

                if not user.check_password(password):
                    print("❌ 비밀번호 틀림")
                    return Response({"detail": "이메일 또는 비밀번호가 올바르지 않습니다."}, status=401)

                refresh = RefreshToken.for_user(user)
                user_data = EmailLoginResponseSerializer(user).data

                print("✅ 로그인 성공")
                return Response(
                    {
                        "message": "이메일 로그인에 성공했습니다.",
                        "access_token": str(refresh.access_token),
                        "refresh_token": str(refresh),
                        "user": user_data,
                    },
                    status=status.HTTP_200_OK,
                )
            except User.DoesNotExist:
                print("❌ 유저 없음")
                return Response({"detail": "이메일 또는 비밀번호가 올바르지 않습니다."}, status=401)
        else:
            print("⚠️ serializer.is_valid() = False")
            print("📝 serializer.errors:", serializer.errors)
            return Response(serializer.errors, status=400)
