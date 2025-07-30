from django.urls import path

<<<<<<< Updated upstream
from apps.users.views.profile_views import UserProfileView

urlpatterns = [
    path("profile/", UserProfileView.as_view(), name="user-profile"),
=======
from .views.auth_code_email_view import SendEmailCodeView, VerifyEmailCodeView
from .views.auth_signup_views import SignupView

urlpatterns = [
    path("auth/signup/", SignupView.as_view(), name="signup"),
    path("auth/send-code/", SendEmailCodeView.as_view(), name="send-email-code"),
    path("auth/verify-code/", VerifyEmailCodeView.as_view(), name="verify-email-code"),
>>>>>>> Stashed changes
]
