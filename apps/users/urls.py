from django.urls import path

from apps.users.views.auth.auth_code_email_view import (
    SendEmailCodeView,
    VerifyEmailCodeView,
)
from apps.users.views.auth.auth_email_login_views import EmailLoginAPIView
from apps.users.views.auth.auth_google_oauth_views import (
    GoogleOAuthCallbackView,
    GoogleOAuthLoginStartView,
)
from apps.users.views.auth.auth_logout_views import LogoutView
from apps.users.views.auth.auth_reset_password_views import (
    ResetPasswordRequestCodeAPIView,
)
from apps.users.views.auth.auth_signup_views import SignupView
from apps.users.views.profile_views import UserProfileView

from .views.auth.auth_find_id_views import FindIDAPIView
from .views.auth.auth_find_password_reset_views import PasswordResetVerifyAPIView
from .views.preference_views import PreferenceSubmitView

urlpatterns = [
    path("profile/", UserProfileView.as_view(), name="user-profile"),
    path("preferences", PreferenceSubmitView.as_view(), name="preference-submit"),
    path("auth/signup/", SignupView.as_view(), name="signup"),
    path("auth/send-code/", SendEmailCodeView.as_view(), name="send-email-code"),
    path("auth/verify-code/", VerifyEmailCodeView.as_view(), name="verify-email-code"),
    path("auth/login/", EmailLoginAPIView.as_view(), name="login"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    path("auth/find-id/", FindIDAPIView.as_view(), name="find-id"),
    path(
        "auth/reset-password/request/",
        ResetPasswordRequestCodeAPIView.as_view(),
        name="비밀번호 재설정 인증 코드 요청(비밀번호 찾기)",
    ),
    path("auth/reset-password/verify/", PasswordResetVerifyAPIView.as_view(), name="인증코드 입력 및 비밀번호 재설정"),
    path("oauth/google/callback/", GoogleOAuthCallbackView.as_view(), name="google-login-callback"),
    path("oauth/google/login/", GoogleOAuthLoginStartView.as_view(), name="google-login-start"),
]
