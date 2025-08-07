# apps/users/serializers/auth/auth_find_password_reset_serializers.py

from typing import Any

from rest_framework import serializers
from rest_framework.serializers import CharField, EmailField, Serializer

from apps.users.models import User
from core.utils.redis_utils import get_restore_email_code


class PasswordResetVerifySerializer(Serializer[Any]):
    email = EmailField()
    verification_code = CharField()
    new_password = CharField(min_length=8)

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        email = data["email"]
        code = data["verification_code"]
        new_password = data["new_password"]

        stored_code = get_restore_email_code(email)
        if not stored_code:
            raise serializers.ValidationError({"detail": "인증 코드가 만료되었거나 존재하지 않습니다."})
        if code != stored_code:
            raise serializers.ValidationError({"detail": "유효하지 않은 인증 코드입니다."})

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError({"detail": "해당 이메일로 등록된 계정이 없습니다."})

        if user.status == "suspended":
            raise serializers.ValidationError({"detail": "계정이 비활성화되었습니다."})
        if user.status == "deleted":
            raise serializers.ValidationError({"detail": "계정이 삭제되었습니다."})

        data["user"] = user
        return data
