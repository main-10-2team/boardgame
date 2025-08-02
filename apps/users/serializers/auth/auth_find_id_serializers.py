# apps/users/serializers/auth/auth_find_id_serializers.py
import re

from rest_framework import serializers


class FindIDRequestSerializer(serializers.Serializer[dict[str, str]]):
    phone_number = serializers.CharField()

    def validate_phone_number(self, value: str) -> str:
        # 국제 전화번호 형식 검사
        if not re.match(r"^\+\d{10,15}$", value):
            raise serializers.ValidationError("유효하지 않은 휴대전화 번호입니다.")
        return value


class FindIDResponseSerializer(serializers.Serializer[dict[str, str]]):
    status = serializers.CharField()
    message = serializers.CharField()
    email = serializers.EmailField()
