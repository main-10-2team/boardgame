# apps/users/serializers/auth/auth_find_password_reset_serializers.py

from typing import Any

from rest_framework import serializers
from rest_framework.serializers import CharField, Serializer

from apps.users.models import User
from core.utils.base62 import generate_base62_code  # 토큰 생성용 함수
from core.utils.redis_utils import (
    delete_reset_email_code,
    get_email_from_reset_token,
    get_restore_email_code,
    store_reset_email_token,
)


# 비밀번호 재설정 - 인증 코드 검증 시리얼라이저
# 이 시리얼라이저는 기존과 동일하게 이메일과 코드를 받습니다.
class PasswordResetVerifyCodeSerializer(Serializer[Any]):
    email = serializers.EmailField()
    verification_code = CharField()

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        # ... 기존 유효성 검사 로직은 그대로 유지 ...
        email = data["email"]
        code = data["verification_code"]

        stored_code = get_restore_email_code(email)
        if not stored_code or code != stored_code:
            raise serializers.ValidationError({"detail": "유효하지 않은 인증 코드입니다."})

        # 인증 성공 시 이메일 대신 임시 토큰을 생성하고 저장합니다.
        token = generate_base62_code()  # 유니크한 토큰 생성
        store_reset_email_token(email, token)  # 토큰과 이메일을 Redis에 연결
        delete_reset_email_code(email)  # 기존 인증 코드는 삭제

        data["token"] = token
        return data


# 비밀번호 재설정 - 새 비밀번호 설정 시리얼라이저 (토큰 기반)
class PasswordResetSetPasswordSerializer(Serializer[Any]):
    reset_token = CharField()  # 이메일 대신 토큰을 받음
    new_password = CharField(min_length=8)

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        token = data["reset_token"]
        new_password = data["new_password"]

        # 1. 토큰으로 이메일 주소를 조회
        email = get_email_from_reset_token(token)
        if not email:
            raise serializers.ValidationError({"detail": "유효하지 않거나 만료된 재설정 링크입니다."})

        # 2. 이메일로 사용자 객체 찾기
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError({"detail": "해당 이메일로 등록된 계정이 없습니다."})

        # 3. 사용자 상태 검증
        if user.status == "suspended":
            raise serializers.ValidationError({"detail": "계정이 비활성화되었습니다."})
        if user.status == "deleted":
            raise serializers.ValidationError({"detail": "계정이 삭제되었습니다."})

        data["user"] = user
        return data
