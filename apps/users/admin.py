# apps/users/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User, SocialAccount, UserPreferencePlaytime, UserPreferenceGenre, AccountDeletionReason


# User 모델을 UserAdmin을 커스텀하여 등록
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    # 'username' 필드가 없으므로 'email'로 대체
    ordering = ('email',)

    # 'is_active'는 속성이므로 필터링 목록에서 제외하고 'status' 필드를 사용
    list_filter = ("role", "status")

    # 'groups'와 'user_permissions' 필드가 없으므로 'filter_horizontal' 제거
    # is_staff, is_superuser 속성을 list_display에 추가하여 상태를 표시
    list_display = (
        "user_id", "email", "nickname", "role", "status", "is_active", "is_staff", "is_superuser"
    )

    # 필드셋 재정의
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (("개인 정보"), {"fields": ("nickname", "name", "profile_image", "birth", "phone_number")}),
        (("권한 및 상태"), {"fields": ("role", "status", "suspended_until")}),
        (("게임 관련 정보"), {"fields": ("review_count", "like_count")})
    )

    # 'UserAdmin'의 기본 'add_fieldsets' 오버라이드
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "nickname", "name", "password"),
            },
        ),
    )

    # 'UserAdmin'의 기본 filter_horizontal 및 readonly_fields 오버라이드
    filter_horizontal = ()
    readonly_fields = ("review_count", "like_count")


# 나머지 모델들도 admin에 등록
# 각 모델별로 커스텀 설정이 필요하다면 아래처럼 Admin 클래스를 정의합니다.
@admin.register(SocialAccount)
class SocialAccountAdmin(admin.ModelAdmin):
    list_display = ("user", "provider", "provider_id", "created_at")
    list_filter = ("provider",)
    search_fields = ("user__email", "provider_id")


@admin.register(UserPreferencePlaytime)
class UserPreferencePlaytimeAdmin(admin.ModelAdmin):
    list_display = ("user", "playtime_category", "created_at")
    list_filter = ("playtime_category",)
    search_fields = ("user__email",)


@admin.register(UserPreferenceGenre)
class UserPreferenceGenreAdmin(admin.ModelAdmin):
    list_display = ("user", "genre", "created_at")
    list_filter = ("genre",)
    search_fields = ("user__email",)


@admin.register(AccountDeletionReason)
class AccountDeletionReasonAdmin(admin.ModelAdmin):
    list_display = ("user", "reason", "created_at")
    list_filter = ("reason",)
    search_fields = ("user__email",)