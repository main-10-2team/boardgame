import logging
import os  # 파일 확장자를 얻기 위해 os 모듈 임포트
import re
import uuid
from datetime import date, datetime
from typing import Any, Dict, List, Set

from django.contrib.auth.hashers import make_password
from django.utils.text import slugify
from rest_framework import serializers
from unidecode import unidecode

from apps.games.models import Genre, PlaytimeCategory
from apps.users.models import User, UserPreferenceGenre, UserPreferencePlaytime
from core.utils.s3_file_upload import S3Uploader

logger = logging.getLogger(__name__)


def korean_slugify(text: str) -> str:
    """
    한글을 포함한 텍스트를 URL 친화적인 slug로 변환합니다.
    """
    ascii_text = unidecode(text)
    return slugify(ascii_text) or "user"


class SignupSerializer(serializers.Serializer):  # type: ignore
    email = serializers.EmailField(max_length=255, required=True)
    password = serializers.CharField(min_length=8, write_only=True, required=True)
    name = serializers.CharField(max_length=10, required=True)
    nickname = serializers.CharField(min_length=2, max_length=20, required=True)
    phone_number = serializers.CharField(max_length=20, required=True)
    birth = serializers.DateField(required=True)
    profile_img_file = serializers.ImageField(
        required=False, allow_null=True, write_only=True, help_text="업로드할 이미지 파일 (JPG/PNG 등)"
    )
    email_verification_code = serializers.CharField(max_length=6, min_length=6, required=True)
     # ID로 받음

    def validate_email(self, value: str) -> str:
        email_regex = r"^[\w\.-]+@([\w-]+\.)+[\w-]{2,4}$"
        if not re.match(email_regex, value):
            raise serializers.ValidationError("invalid_email")
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("duplicate_email")
        return value

    def validate_nickname(self, value: str) -> str:
        if not (2 <= len(value) <= 20):
            raise serializers.ValidationError("invalid_nickname")
        if User.objects.filter(nickname=value).exists():
            raise serializers.ValidationError("duplicate_nickname")
        return value

    def validate_phone_number(self, value: str) -> str:
        phone_regex = r"^\+\d{1,3}\d{9,12}$"
        if not re.match(phone_regex, value):
            raise serializers.ValidationError("invalid_phone_number")
        if User.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError("duplicate_phone_number")
        return value

    def validate_birth(self, value: date) -> date:
        if value < date(1900, 1, 1) or value > date.today():
            raise serializers.ValidationError("invalid_birth")
        return value

    def create(self, validated_data: Dict[str, Any]) -> User:
        email_verification_code = validated_data.pop("email_verification_code")
        preferred_genres = validated_data.pop("preferred_genres", [])
        preferred_playtime_objects = validated_data.pop("preferred_playtime", [])
        profile_img_file = validated_data.pop("profile_img_file", None)
        validated_data["password"] = make_password(validated_data["password"])
        validated_data["role"] = "user"
        validated_data["status"] = "active"
        validated_data["created_at"] = datetime.now()
        validated_data["updated_at"] = datetime.now()

        s3_uploader = S3Uploader()
        uploaded_s3_key = None  # 롤백을 위한 S3 키 변수 초기화
        user = None

        try:
            # 사용자 생성 (profile_image는 아직 할당하지 않음)
            user = User.objects.create(**validated_data)

            # 프로필 이미지 파일 처리 (닉네임 기반 파일명 생성)
            if profile_img_file:
                nickname_slug = korean_slugify(validated_data.get("nickname", "anonymous"))
                file_extension = os.path.splitext(profile_img_file.name)[1] or ".jpg"
                unique_name = f"{uuid.uuid4().hex[:6]}_{nickname_slug}{file_extension}"
                s3_key = f"profile_images/{unique_name}"

                profile_image_url = s3_uploader.upload_file(file_obj=profile_img_file, s3_key=s3_key)

                if profile_image_url:
                    user.profile_image = s3_key  # S3 Key를 저장합니다.
                    user.save(update_fields=["profile_image"])
                    uploaded_s3_key = s3_key  # 롤백을 위해 S3 키 저장
                else:
                    logger.error(f"S3 프로필 이미지 업로드 실패: {profile_img_file.name}")
                    raise serializers.ValidationError({"detail": "프로필 이미지 업로드에 실패했습니다."})

            if preferred_genres:
                user_preference_genres = [
                    UserPreferenceGenre(user=user, genre=genre_obj, created_at=datetime.now())
                    for genre_obj in preferred_genres
                ]
                UserPreferenceGenre.objects.bulk_create(user_preference_genres)

            if preferred_playtime_objects:
                user_preference_playtimes = [
                    UserPreferencePlaytime(user=user, playtime_category=playtime_obj, created_at=datetime.now())
                    for playtime_obj in preferred_playtime_objects
                ]
                UserPreferencePlaytime.objects.bulk_create(user_preference_playtimes)

            return user

        except Exception as e:
            # 예외 발생 시 업로드된 S3 파일 롤백
            if uploaded_s3_key:
                try:
                    s3_uploader.delete_file(uploaded_s3_key)
                    logger.info(f"S3 롤백 성공: {uploaded_s3_key}")
                except Exception as delete_err:
                    logger.error(f"S3 롤백 실패: {uploaded_s3_key}, 오류: {delete_err}")

            # 이미 생성된 user 객체가 있다면 삭제하여 롤백
            if user and user.pk:
                user.delete()
                logger.info(f"유저 롤백 성공: {user.email}")

            # 기존 오류를 다시 발생시킵니다.
            logger.exception("회원가입 처리 중 오류 발생")
            raise serializers.ValidationError({"non_field_errors": [f"회원가입 처리 중 오류가 발생했습니다: {str(e)}"]})
