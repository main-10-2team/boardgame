from django.contrib.auth.base_user import AbstractBaseUser
from django.db import models

from apps.games.models import Genre, PlaytimeCategory


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
    email = models.EmailField(unique=True, null=False)
    password = models.CharField(max_length=128, null=False)  # Store hashed passwords
    nickname = models.CharField(max_length=20, unique=True, null=False, help_text="2-20 characters")
    birth = models.DateTimeField(null=False)
    phone_number = models.CharField(max_length=20, null=False)
    role = models.CharField(max_length=5, choices=ROLE_CHOICES, default="user")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["nickname", "birth", "phone_number"]

    class Meta:
        db_table = "user"
        verbose_name = "사용자"
        verbose_name_plural = "사용자 목록"


class SocialAccount(models.Model):
    social_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=False)
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


class UserPreferencePlaytime(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)  # One-to-one relationship
    playtime_category = models.ForeignKey(PlaytimeCategory, on_delete=models.CASCADE)
    created_at = models.DateTimeField(
        auto_now_add=True, null=True
    )  # Allowing null initially based on ERD, but auto_now_add is usually not null
    updated_at = models.DateTimeField(
        auto_now=True, null=True
    )  # Allowing null initially based on ERD, but auto_now is usually not null

    class Meta:
        db_table = "user_preference_playtime"
        verbose_name = "선호하는 게임 시간"
        verbose_name_plural = "선호하는 게임 시간 목록"


class UserPreferenceGenre(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=False)
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE, null=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "user_preference_genre"
        verbose_name = "사용자 선호하는 장르"
        verbose_name_plural = "사용자 선호하는 장르 목록"
        unique_together = ("user", "genre")
