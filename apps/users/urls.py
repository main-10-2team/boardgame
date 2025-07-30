from django.urls import path

from apps.users.views.profile_views import UserProfileView

urlpatterns = [
    path("profile/", UserProfileView.as_view(), name="user-profile"),
]
