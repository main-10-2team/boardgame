import logging
import os
import uuid
from typing import Any

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.files.uploadedfile import UploadedFile
from django.db.models import Count
from django.utils.text import slugify
from rest_framework import serializers
from unidecode import unidecode

from apps.games.models import Genre
from apps.users.models import User
from core.utils.account_delete_reason import AccountDeletionReasonEnum
from core.utils.s3_file_upload import S3Uploader

logger = logging.getLogger(__name__)


def korean_slugify(text: str) -> str:
    ascii_text = unidecode(text)
    return slugify(ascii_text) or "user"


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
            "phone_number",
            "birth",
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
                    base_url = f"{uploader.client.meta.endpoint_url}/{uploader.bucket}"
                    existing_url = f"{base_url}/{existing_key}"
                    updated_url = uploader.update_file(profile_image, existing_url)
                    if not updated_url:
                        raise serializers.ValidationError(
                            {"non_field_errors": ["프로필 이미지 업로드에 실패했습니다."]}
                        )
                    uploaded_s3_key = updated_url
                    instance.profile_image = existing_key
                else:
                    nickname = korean_slugify(instance.nickname or "anonymous")
                    extension = os.path.splitext(profile_image.name or "default.jpg")[1] or ".jpg"
                    unique_name = f"{uuid.uuid4().hex[:6]}_{nickname}{extension}"
                    s3_key = f"profile_images/{unique_name}"
                    uploaded_url = uploader.upload_file(profile_image, s3_key)
                    if not uploaded_url:
                        raise serializers.ValidationError(
                            {"non_field_errors": ["프로필 이미지 업로드에 실패했습니다."]}
                        )
                    uploaded_s3_key = s3_key
                    instance.profile_image = s3_key

            instance.save()
            return instance

        except serializers.ValidationError as ve:
            raise ve

        except Exception as e:
            if uploaded_s3_key:
                try:
                    uploader.delete_file(uploaded_s3_key)
                    logger.info(f"S3 롤백 성공: {uploaded_s3_key}")
                except Exception as delete_err:
                    logger.error(f"S3 롤백 실패: {uploaded_s3_key}, 오류: {delete_err}")

            logger.exception("유저 프로필 수정 중 오류 발생")
            raise serializers.ValidationError({"non_field_errors": [f"프로필 수정 중 오류가 발생했습니다: {str(e)}"]})


class PasswordChangeSerializer(serializers.Serializer[Any]):
    current_password = serializers.CharField()
    new_password = serializers.CharField()
    new_password_confirm = serializers.CharField()

    class Meta:
        ref_name = "PasswordChange"

    def validate_current_password(self, value: str) -> str:
        user: User = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("현재 비밀번호가 일치하지 않습니다.")
        return value

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        pw1 = attrs.get("new_password")
        pw2 = attrs.get("new_password_confirm")
        current_pw = attrs.get("current_password")

        if pw1 != pw2:
            raise serializers.ValidationError({"new_password_confirm": "비밀번호가 서로 일치하지 않습니다."})

        if pw1 == current_pw:
            raise serializers.ValidationError(
                {"new_password": "현재 비밀번호와 동일한 비밀번호로는 변경할 수 없습니다."}
            )

        if not isinstance(pw1, str):
            raise serializers.ValidationError({"new_password": "비밀번호는 문자열이어야 합니다."})

        try:
            validate_password(pw1, self.context["request"].user)
        except DjangoValidationError as e:
            raise serializers.ValidationError({"new_password": e.messages})

        return attrs

    def save(self, **kwargs: Any) -> None:
        user: User = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save()


class AccountDeleteSerializer(serializers.Serializer[Any]):
    password = serializers.CharField()
    reason = serializers.ChoiceField(choices=AccountDeletionReasonEnum.choices())
    additional_text = serializers.CharField(required=False, allow_blank=True, min_length=5, max_length=500)

    class Meta:
        ref_name = "AccountDelete"

    def validate_password(self, value: str) -> str:
        user: User = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError({"detail": "비밀번호가 일치하지 않습니다."})
        return value

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        reason = attrs.get("reason")
        additional_text = attrs.get("additional_text", "").strip()

        if reason == AccountDeletionReasonEnum.OTHER:
            if not additional_text:
                raise serializers.ValidationError({"detail": "기타 사유를 입력해 주세요."})
            if len(additional_text) < 5:
                raise serializers.ValidationError({"detail": "기타 사유는 최소 5자 이상이어야 합니다."})
            if len(additional_text) > 500:
                raise serializers.ValidationError({"detail": "기타 사유는 최대 500글자 입니다."})

        return attrs
