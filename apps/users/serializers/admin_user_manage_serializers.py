from typing import TypeAlias

from django.db.models import Model  # 이 부분을 추가해야 합니다.
from rest_framework import serializers

from apps.users.models import User


# Mypy가 User 모델을 인지할 수 있도록 생성
# 관리자 회원 정보 조회
class AdminUserdetailSerializer(serializers.ModelSerializer[User]):

    # API 명세서의 "id" 필드는 User 모델의 "user_id"에 해당합니다.
    id = serializers.IntegerField(source="user_id", read_only=True)

    # API 명세서의 "username" 필드는 User 모델의 "nickname"에 해당합니다.
    username = serializers.CharField(source="nickname", read_only=True)

    email = serializers.EmailField(read_only=True)

    created_at = serializers.DateTimeField(read_only=True, format="%Y-%m-%d %H:%M:%S")

    # Django의 AbstractBaseUser에 기본적으로 포함된 last_login 필드를 사용합니다.
    last_login = serializers.DateTimeField(read_only=True, format="%Y-%m-%d %H:%M:%S")

    class Meta:

        model = User
        fields = ("id", "username", "email", "created_at", "last_login")
