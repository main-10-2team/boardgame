import secrets
from urllib.parse import urlencode

import requests
from django.conf import settings
from django.shortcuts import redirect
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.models import SocialAccount, User
from core.utils.jwt import generate_jwt_token_pair


@extend_schema(
    tags=["인증"],
    summary="Google 소셜 로그인 시작",
    description="Google OAuth 2.0 로그인을 시작하고, 구글 인증 페이지로 리디렉션합니다.",
    responses={
        302: OpenApiResponse(description="Google 로그인 페이지로 리디렉션"),
    },
    parameters=[
        OpenApiParameter(
            name="state",
            required=False,
            type=str,
            location=OpenApiParameter.QUERY,
            description="CSRF 방지를 위한 상태 값 (자동 생성됨)",
        ),
    ],
)
class GoogleOAuthLoginStartView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, *args, **kwargs):  # type: ignore
        state = secrets.token_urlsafe(16)
        request.session["oauth_state"] = state  # CSRF 방지

        params = {
            "response_type": "code",
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "scope": "openid email profile",
            "state": state,
            "access_type": "offline",
            "prompt": "consent",
        }
        auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
        return redirect(auth_url)


@extend_schema(
    tags=["인증"],
    summary="Google 소셜 로그인 콜백",
    description=(
        "구글에서 인증 후 리디렉션되는 콜백 URL입니다. "
        "authorization code와 state를 받아 액세스 토큰을 교환하고, 사용자 정보를 가져와 회원가입 또는 로그인을 처리합니다."
    ),
    parameters=[
        OpenApiParameter(
            name="code",
            required=True,
            type=str,
            location=OpenApiParameter.QUERY,
            description="구글이 전달한 authorization code",
        ),
        OpenApiParameter(
            name="state",
            required=True,
            type=str,
            location=OpenApiParameter.QUERY,
            description="로그인 시작 시 설정한 state 값",
        ),
    ],
    responses={
        302: OpenApiResponse(description="프론트엔드로 access_token, refresh_token을 포함한 URL로 리디렉션"),
        400: OpenApiResponse(description="state 불일치 또는 사용자 정보 오류"),
    },
)
class GoogleOAuthCallbackView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, *args, **kwargs):  # type: ignore
        code = request.GET.get("code")
        state = request.GET.get("state")
        stored_state = request.session.get("oauth_state")

        if not code or not state or stored_state != state:
            return Response({"error": "Invalid state or missing code"}, status=status.HTTP_400_BAD_REQUEST)

        # 1. Google access_token 요청
        try:
            token_response = requests.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                    "grant_type": "authorization_code",
                },
            )
            token_response.raise_for_status()
            token_data = token_response.json()
            access_token = token_data.get("access_token")
        except requests.RequestException:
            return Response({"error": "Failed to get access token"}, status=status.HTTP_400_BAD_REQUEST)

        # 2. 유저 정보 요청
        try:
            userinfo_response = requests.get(
                "https://www.googleapis.com/oauth2/v3/userinfo", headers={"Authorization": f"Bearer {access_token}"}
            )
            userinfo_response.raise_for_status()
            userinfo = userinfo_response.json()
        except requests.RequestException:
            return Response({"error": "Failed to get user info"}, status=status.HTTP_400_BAD_REQUEST)

        email = userinfo.get("email")
        name = userinfo.get("name", "User")
        picture = userinfo.get("picture")
        provider_id = userinfo.get("sub")

        if not email or not provider_id:
            return Response({"error": "Invalid user info"}, status=status.HTTP_400_BAD_REQUEST)

        # 3. 기존 유저 확인 or 생성
        try:
            social_account = SocialAccount.objects.select_related("user").get(
                provider="google", provider_id=provider_id
            )
            user = social_account.user
        except SocialAccount.DoesNotExist:
            base_nickname = name.replace(" ", "")
            nickname = base_nickname
            while User.objects.filter(nickname=nickname).exists():
                nickname = f"{base_nickname}_{secrets.randbelow(1000)}"

            user = User.objects.create_user(
                email=email,
                password="social_dummy_password",
                nickname=nickname,
                birth="1970-01-01",
                phone_number="+820000000000",
                role="user",
                status="active",
            )

            SocialAccount.objects.create(
                user=user,
                provider="google",
                provider_id=provider_id,
                profile_url=picture,
            )

        # 4. JWT 토큰 발급
        access_token_jwt, refresh_token = generate_jwt_token_pair(user)

        # 5. 결과 응답 or 프론트 리디렉트
        # frontend_url = settings.APP_FRONTEND_URL or "http://localhost:3000"
        # redirect_url = f"{frontend_url}/oauth/callback?access_token={access_token_jwt}&refresh_token={refresh_token}"
        # return redirect(redirect_url)
        return Response({"access_token": access_token_jwt, "refresh_token": refresh_token}, status=status.HTTP_200_OK)
