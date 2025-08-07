from django.contrib.auth.base_user import AbstractBaseUser
from django.db import models

from apps.games.models import Genre, PlaytimeCategory
from apps.users.manage import CustomUserManager
from core.utils.account_delete_reason import AccountDeletionReasonEnum


class User(AbstractBaseUser):

    ROLE_CHOICES = [
        ("user", "User"),
        ("admin", "Admin"),
    ]
    STATUS_CHOICES = [
        ("active", "Active"),
        ("suspended", "Suspended"),
        ("deleted", "Deleted"),
    ]

    user_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=30)
    email = models.EmailField(unique=True, null=False)
    nickname = models.CharField(max_length=20, unique=True, null=False, help_text="2-20 characters")
    profile_image = models.URLField(null=True, blank=True)
    preferred_genres = models.ManyToManyField(
        "games.Genre", through="UserPreferenceGenre", related_name="preferred_by_users", blank=True
    )  # type: ignore
    preferred_playtimes = models.ManyToManyField(
        "games.PlaytimeCategory", through="UserPreferencePlaytime", related_name="preferred_by_users", blank=True
    )  # type: ignore
    review_count = models.PositiveSmallIntegerField(default=0)
    like_count = models.PositiveSmallIntegerField(default=0)
    birth = models.DateTimeField(null=False)
    phone_number = models.CharField(max_length=20, null=False)
    role = models.CharField(max_length=5, choices=ROLE_CHOICES, default="user")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="active")
    suspended_until = models.DateTimeField(null=True, blank=True, help_text="사용자 차단 기간 (NULL이면 영구 정지)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["nickname", "birth", "phone_number"]
    objects = CustomUserManager()

    @property
    def is_staff(self):
        """role이 'admin'인 경우 True를 반환하여 Admin 페이지 접근을 허용"""
        return self.role == "admin"

    @property
    def is_superuser(self):
        """role이 'admin'인 경우 True를 반환하여 최고 관리자 권한을 부여"""
        return self.role == "admin"

    @property
    def is_active(self):
        """status가 'active'인 경우 True를 반환하여 계정 활성화 상태를 표시"""
        return self.status == "active"

    def has_perm(self, perm, obj=None):
        "사용자가 특정 권한을 가지고 있는지 여부"
        # 단순화를 위해, admin 역할이면 모든 권한을 가진다고 가정
        return self.is_superuser

    def has_module_perms(self, app_label):
        "사용자가 특정 앱에 대한 권한을 가지고 있는지 여부"
        # 단순화를 위해, admin 역할이면 모든 앱에 대한 권한을 가진다고 가정
        return self.is_superuser

    class Meta:
        db_table = "user"
        verbose_name = "사용자"
        verbose_name_plural = "사용자 목록"

    def __str__(self) -> str:
        return f"{self.nickname} ({self.email})"


class SocialAccount(models.Model):
    social_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=False, related_name="social_accounts")
    provider = models.CharField(max_length=50, null=False, help_text='e.g., "google"')
    provider_id = models.CharField(max_length=255, null=False, help_text="Google user ID")
    profile_url = models.CharField(max_length=255, null=True, blank=True, help_text="Profile picture URL")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "social_account"
        verbose_name = "소셜 어카운트"
        verbose_name_plural = "소셜 어카운트 목록"
        unique_together = ("provider", "provider_id")

    def __str__(self) -> str:
        return f"{self.user.email} - {self.provider}"


class UserPreferencePlaytime(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=False, related_name="user_preferred_playtimes")
    playtime_category = models.ForeignKey(PlaytimeCategory, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        db_table = "user_preference_playtime"
        verbose_name = "선호하는 게임 시간"
        verbose_name_plural = "선호하는 게임 시간 목록"
        unique_together = ("user", "playtime_category")

    def __str__(self) -> str:
        return f"{self.user.nickname} prefers {self.playtime_category.name}"


class UserPreferenceGenre(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=False, related_name="user_preferred_genres")
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE, null=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "user_preference_genre"
        verbose_name = "사용자 선호하는 장르"
        verbose_name_plural = "사용자 선호하는 장르 목록"
        unique_together = ("user", "genre")

    def __str__(self) -> str:
        return f"{self.user.nickname} prefers {self.genre.name}"


class AccountDeletionReason(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="deletion_reason")
    reason = models.CharField(max_length=50, choices=AccountDeletionReasonEnum.choices())
    additional_text = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "account_deletion_reason"
        verbose_name = "회원 탈퇴 사유"
        verbose_name_plural = "회원 탈퇴 사유 목록"

    def __str__(self) -> str:
        return f"{self.user.email} - {self.reason}"
