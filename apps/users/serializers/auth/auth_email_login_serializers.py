from typing import Any, Optional, cast

from django.contrib.auth import authenticate
from django.db.models.fields.files import ImageFieldFile
from django.views.decorators.csrf import csrf_exempt
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from apps.users.models import User


class EmailLoginSerializer(serializers.Serializer[Any]):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        email = attrs.get("email")
        password = attrs.get("password")

        # 사용자 인증
        user = authenticate(email=email, password=password)
        if not user:
            raise ValidationError("이메일 또는 비밀번호가 올바르지 않습니다.")

        # ✅ status 체크: active만 로그인 가능
        if user.status != "active":
            raise ValidationError("비활성화된 계정입니다. 관리자에게 문의하세요.")

        # 유효한 사용자일 경우 attrs에 저장
        attrs["user"] = user
        return attrs


class EmailLoginResponseSerializer(serializers.ModelSerializer[Any]):
    profile_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "user_id",
            "email",
            "nickname",
            "phone_number",
            "birth",
            "role",
            "status",
            "profile_url",
        )

    def get_profile_url(self, obj: User) -> Optional[str]:
        profile_image = obj.profile_image
        if isinstance(profile_image, ImageFieldFile) and profile_image.name:
            return str(profile_image.url)
        return None
