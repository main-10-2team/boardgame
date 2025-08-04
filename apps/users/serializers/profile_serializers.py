import logging
import uuid
from typing import Any

from django.core.files.uploadedfile import UploadedFile
from django.db.models import Count
from rest_framework import serializers

from apps.games.models import Genre
from apps.users.models import User
from core.utils.s3_file_upload import S3Uploader

logger = logging.getLogger(__name__)


class UserProfileSerializer(serializers.ModelSerializer[User]):
    preferred_genres = serializers.SerializerMethodField()
    preferred_playtimes = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()
    like_count = serializers.SerializerMethodField()
    popular_genres = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "name",
            "email",
            "nickname",
            "profile_image",
            "review_count",
            "like_count",
            "created_at",
            "preferred_genres",
            "preferred_playtimes",
            "popular_genres",
        ]

        read_only_fields = fields

    def get_review_count(self, obj: User) -> int:
        return obj.reviews.all().count()

    def get_like_count(self, obj: User) -> int:
        return obj.likes.all().count()

    def get_preferred_genres(self, obj: User) -> list[str]:
        return [genre.name for genre in obj.preferred_genres.all()]

    def get_preferred_playtimes(self, obj: User) -> list[str]:
        return [pt.name for pt in obj.preferred_playtimes.all()]

    def get_popular_genres(self, obj: User) -> list[str]:
        genre_qs = (
            Genre.objects.filter(genre_games__game__liked_by_users__user=obj)
            .annotate(like_count=Count("genre_games__game__liked_by_users"))
            .order_by("-like_count")[:10]
        )

        if not genre_qs.exists():
            return []

        return [genre.name for genre in genre_qs]


class UserProfileUpdateSerializer(serializers.ModelSerializer[User]):
    nickname = serializers.CharField(required=False)
    phone_number = serializers.CharField(required=False)
    profile_image = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = ["nickname", "phone_number", "profile_image"]

    def validate_nickname(self, value: str) -> str:
        user: User = self.context["request"].user
        if User.objects.exclude(pk=user.pk).filter(nickname=value).exists():
            raise serializers.ValidationError("이미 사용 중인 닉네임입니다.")
        return value

    def update(self, instance: User, validated_data: dict[str, Any]) -> User:
        uploader = S3Uploader()
        uploaded_s3_key = None

        try:
            if "nickname" in validated_data:
                instance.nickname = validated_data["nickname"]

            if "phone_number" in validated_data:
                instance.phone_number = validated_data["phone_number"]

            if "profile_image" in self.context["request"].FILES:
                profile_image: UploadedFile = self.context["request"].FILES["profile_image"]
                if instance.profile_image:
                    existing_key = str(instance.profile_image)
                    updated_key = uploader.update_file(profile_image, existing_key)
                    if not updated_key:
                        raise serializers.ValidationError("프로필 이미지 업데이트에 실패했습니다.")
                    uploaded_s3_key = existing_key
                else:
                    unique_name = f"{uuid.uuid4().hex[:6]}_{profile_image.name}"
                    s3_key = f"profile_images/{uuid.uuid4()}_{unique_name}"
                    uploaded_url = uploader.upload_file(profile_image, s3_key)
                    if not uploaded_url:
                        raise serializers.ValidationError("프로필 이미지 업로드에 실패했습니다.")
                    uploaded_s3_key = s3_key
                    instance.profile_image = s3_key

            instance.save()
            return instance

        except Exception as e:
            if uploaded_s3_key:
                try:
                    uploader.delete_file(uploaded_s3_key)
                    logger.info(f"S3 롤백 성공: {uploaded_s3_key}")
                except Exception as delete_err:
                    logger.error(f"S3 롤백 실패: {uploaded_s3_key}, 오류: {delete_err}")

            logger.exception("유저 프로필 수정 중 오류 발생")
            raise serializers.ValidationError({"non_field_errors": [f"프로필 수정 중 오류가 발생했습니다: {e}"]})
