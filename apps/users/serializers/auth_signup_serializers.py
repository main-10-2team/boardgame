import os  # 파일 확장자를 얻기 위해 os 모듈 임포트
import re

# S3 파일 업로드를 위한 임포트
import uuid
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Set

from django.contrib.auth.hashers import make_password
from drf_spectacular.types import OpenApiTypes
from rest_framework import serializers

from apps.games.models import Genre, PlaytimeCategory
from apps.users.models import User, UserPreferenceGenre, UserPreferencePlaytime
from core.utils.s3_file_upload import S3Uploader  # S3Uploader 클래스 임포트


class SignupSerializer(serializers.Serializer):#type: ignore
    email = serializers.EmailField(max_length=255, required=True)
    password = serializers.CharField(min_length=8, write_only=True, required=True)
    nickname = serializers.CharField(min_length=2, max_length=20, required=True)
    phone_number = serializers.CharField(max_length=20, required=True)
    birth = serializers.DateField(required=True)
    profile_img_file = serializers.ImageField(
        required=False, allow_null=True, write_only=True, help_text="업로드할 이미지 파일 (JPG/PNG 등)"
    )
    email_verification_code = serializers.CharField(max_length=6, min_length=6, required=True)
    preferred_genres = serializers.ListField(child=serializers.IntegerField(), required=False, default=[])  # ID로 받음
    preferred_playtime = serializers.ListField(
        child=serializers.IntegerField(), required=False, default=[]
    )  # ID로 받음

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

    def validate_preferred_genres(self, value: List[int]) -> List[Genre]:
        """
        선호 장르 ID 목록을 받아 유효성을 검사하고, 해당 Genre 객체 목록을 반환합니다.
        """
        if not value:
            return []

        requested_genre_ids: Set[int] = set(value)
        genres = list(Genre.objects.filter(genre_id__in=requested_genre_ids))
        valid_genre_ids: Set[int] = {genre.genre_id for genre in genres}

        if requested_genre_ids != valid_genre_ids:
            invalid_ids = requested_genre_ids - valid_genre_ids
            raise serializers.ValidationError(f"invalid_genre_id: {', '.join(map(str, invalid_ids))}")
        return genres

    def validate_preferred_playtime(self, value: List[int]) -> List[PlaytimeCategory]:
        """
        선호 플레이 시간 ID를 받아 유효성을 검사하고, 해당 PlaytimeCategory 객체를 반환합니다.
        """
        if not value:  # 리스트가 비어있으면 빈 리스트 반환
            return []

        requested_playtime_ids: Set[int] = set(value)
        # 이 부분이 핵심입니다: PlaytimeCategory.objects.get(...) 대신 filter(playtime_id__in=...) 사용
        playtimes = list(PlaytimeCategory.objects.filter(playtime_id__in=requested_playtime_ids))
        valid_playtime_ids: Set[int] = {p.playtime_id for p in playtimes}

        if requested_playtime_ids != valid_playtime_ids:
            invalid_ids = requested_playtime_ids - valid_playtime_ids
            raise serializers.ValidationError(f"invalid_playtime_id: {', '.join(map(str, invalid_ids))}")
        return playtimes  # PlaytimeCategory 객체들의 리스트를 반환

    def create(self, validated_data: Dict[str, Any]) -> User:
        email_verification_code = validated_data.pop("email_verification_code")
        preferred_genres = validated_data.pop(
            "preferred_genres", []
        )  # 기본값 [] 추가 (validated_data에 없을 수도 있으므로)
        # preferred_playtime이 이제 PlaytimeCategory 객체들의 리스트입니다. 변수명을 더 명확하게 변경합니다.
        preferred_playtime_objects = validated_data.pop(
            "preferred_playtime", []
        )  # 기본값 [] 추가 및 변수명 변경 (객체 리스트임을 명시)
        profile_img_file = validated_data.pop("profile_img_file", None)
        validated_data["password"] = make_password(validated_data["password"])
        validated_data["role"] = "user"
        validated_data["status"] = "active"
        validated_data["created_at"] = datetime.now()
        validated_data["updated_at"] = datetime.now()

        # 사용자 생성
        user = User.objects.create(**validated_data)

        # 프로필 이미지 파일 처리 (S3Uploader 사용)
        if profile_img_file:
            s3_uploader = S3Uploader()
            file_extension = os.path.splitext(profile_img_file.name)[1]
            s3_key = f"profile_images/{uuid.uuid4()}{file_extension}"
            profile_image_url = s3_uploader.upload_file(file_obj=profile_img_file, s3_key=s3_key)

            if profile_image_url:
                user.profile_image = profile_image_url
                user.save(update_fields=["profile_image"])
            else:
                import logging

                logger = logging.getLogger(__name__)
                logger.error(f"S3 프로필 이미지 업로드 실패: {profile_img_file.name}")
                # S3 업로드 실패 시 사용자 롤백 (선택 사항)
                # user.delete()
                # raise serializers.ValidationError({"detail": "프로필 이미지 업로드에 실패했습니다."})

        if preferred_genres:
            # 여러 개의 UserPreferenceGenre 객체를 한 번에 생성합니다.
            user_preference_genres = [
                UserPreferenceGenre(user=user, genre=genre_obj, created_at=datetime.now())
                for genre_obj in preferred_genres
            ]
            UserPreferenceGenre.objects.bulk_create(user_preference_genres)

        # 이 부분이 수정되어야 합니다.
        if preferred_playtime_objects:  # preferred_playtime_objects는 PlaytimeCategory 객체들의 리스트입니다.
            # 각 PlaytimeCategory 객체에 대해 UserPreferencePlaytime 객체를 생성하고 bulk_create를 사용합니다.
            user_preference_playtimes = [
                UserPreferencePlaytime(user=user, playtime_category=playtime_obj, created_at=datetime.now())
                for playtime_obj in preferred_playtime_objects
            ]
            UserPreferencePlaytime.objects.bulk_create(user_preference_playtimes)  #

        return user
