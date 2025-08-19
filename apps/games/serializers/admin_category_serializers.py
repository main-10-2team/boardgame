from typing import Any, Optional, cast

from django.db import IntegrityError  # IntegrityError
from rest_framework import serializers

from apps.games.models import Category, GameCategory


# 관리자 카테고리 등록 시리얼라이저
class AdminCategoryCreateSerializer(serializers.ModelSerializer[Category]):

    # Category 모델과 연동하여 데이터를 직렬화하고 유효성을 검사합니다.
    id = serializers.IntegerField(source="category_id", read_only=True, help_text="등록된 카테고리의 고유 ID")
    name = serializers.CharField(max_length=255, help_text="카테고리의 고유한 이름")
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True, help_text="정보 생성일시")
    updated_at = serializers.DateTimeField(
        format="%Y-%m-%d %H:%M:%S", read_only=True, help_text="정보 최종 업데이트 일시"
    )

    class Meta:
        model = Category
        fields = ["id", "name", "created_at", "updated_at"]
        extra_kwargs = {
            "name": {"required": True},
        }

    # 카테고리 이름의 고유성을 검사합니다.
    def validate_name(self, value: str) -> str:

        if Category.objects.filter(name=value).exists():
            raise serializers.ValidationError("이미 동일한 이름의 카테고리가 등록되어 있습니다.")
        return value


# 관리자 카테고리 수정 시리얼라이저 (PATCH 요청용)
class AdminCategoryUpdateSerializer(serializers.ModelSerializer[Category]):

    # PATCH 요청을 위해 모든 필드를 선택적으로 설정하고, 응답 필드를 포함합니다.
    id = serializers.IntegerField(source="category_id", read_only=True, help_text="수정된 카테고리의 고유 ID")
    name = serializers.CharField(
        max_length=255, required=False, help_text="카테고리의 고유한 이름 (변경 시 유일해야 함)"
    )
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True, help_text="정보 생성일시")
    updated_at = serializers.DateTimeField(
        format="%Y-%m-%d %H:%M:%S", read_only=True, help_text="정보 최종 업데이트 일시"
    )

    class Meta:
        model = Category
        fields = ["id", "name", "created_at", "updated_at"]

    # 카테고리 이름의 고유성을 검사합니다.
    def validate_name(self, value: str) -> str:

        # 수정 시에는 현재 인스턴스의 이름이 아닌 다른 카테고리의 이름과 중복되는지 확인합니다.
        if self.instance:
            current_category_instance = cast(Category, self.instance)
            if Category.objects.filter(name=value).exclude(pk=current_category_instance.pk).exists():
                raise serializers.ValidationError("이미 동일한 이름의 카테고리가 등록되어 있습니다.")
        elif Category.objects.filter(name=value).exists():
            raise serializers.ValidationError("이미 동일한 이름의 카테고리가 등록되어 있습니다.")
        return value


# 관리자 카테고리 목록 조회 API를 위한 시리얼라이저
class AdminCategoryListSerializer(serializers.ModelSerializer[Category]):

    id = serializers.IntegerField(source="category_id", read_only=True, help_text="카테고리의 고유 ID")
    name = serializers.CharField(max_length=255, help_text="카테고리의 이름")
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True, help_text="정보 생성일시")
    updated_at = serializers.DateTimeField(
        format="%Y-%m-%d %H:%M:%S", read_only=True, help_text="정보 최종 업데이트 일시"
    )

    class Meta:
        model = Category
        fields = ["id", "name", "created_at", "updated_at"]


class AdminCategoryDeleteSerializer(serializers.ModelSerializer[Category]):
    id = serializers.IntegerField(source="category_id", read_only=True)
    message = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ["id", "message"]