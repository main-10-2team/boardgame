from datetime import timedelta
from typing import Any, Dict, TypeAlias

from django.contrib.auth import get_user_model
from django.db.models import Model
from django.utils import timezone
from rest_framework import serializers

from apps.users.models import User

# Mypy가 User 모델을 인지할 수 있도록 생성
# 관리자 회원 정보 조회

user = get_user_model()


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

    # 회원 제재(활동 정지)


class UserSuspendSerializer(serializers.ModelSerializer[User]):  # <-- 여기에 [User] 추가

    reason = serializers.CharField(
        max_length=500, required=True, write_only=True, help_text="제재 사유 (예: '욕설', '불법 광고')"
    )
    duration = serializers.IntegerField(
        required=False, min_value=0, write_only=True, help_text="제재 기간 (일 단위). 0 또는 생략 시 영구 제재"
    )

    class Meta:
        model = User
        fields = ["status", "suspended_until", "reason", "duration"]
        read_only_fields = ["status", "suspended_until"]

    def validate_duration(self, value: Any) -> Any:
        if value is not None and value < 0:
            raise serializers.ValidationError("duration은 음수일 수 없습니다.")
        return value

    def update(self, instance: User, validated_data: Dict[str, Any]) -> User:
        # reason과 duration은 write_only 필드이므로 validated_data에서 pop하여 사용
        reason = validated_data.pop("reason", None)
        duration = validated_data.pop("duration", None)

        instance.status = "suspended"
        if duration is not None and duration > 0:
            instance.suspended_until = timezone.now() + timedelta(days=duration)
        else:
            instance.suspended_until = None

        # User 모델에 제재 사유를 저장할 필드(예: suspension_reason)가 있다면 여기에 저장
        # instance.suspension_reason = reason

        instance.save()
        return instance


class UserDeactivateSerializer(serializers.ModelSerializer[User]):

    # 회원 탈퇴(영구 삭제) API 요청 바디를 위한 ModelSerializer입니다.

    reason = serializers.CharField(
        max_length=500, required=True, write_only=True, help_text="탈퇴 사유 (관리자 측 기록용)"
    )
    delete_data = serializers.BooleanField(
        required=False, default=False, write_only=True, help_text="회원의 모든 관련 데이터 영구 삭제 여부"
    )

    class Meta:
        model = User
        fields = ["status", "reason", "delete_data"]
        read_only_fields = ["status"]  # 뷰에서 직접 업데이트하므로 읽기 전용으로 설정

    def update(self, instance: User, validated_data: Dict[str, Any]) -> User:
        reason = validated_data.pop("reason", None)
        delete_data = validated_data.pop("delete_data", False)

        instance.status = "deleted"
        # User 모델의 is_active 속성이 status에 따라 자동 변경됩니다.

        # User 모델에 탈퇴 사유를 저장할 필드(예: deactivation_reason)가 있다면 여기에 저장
        # instance.deactivation_reason = reason

        instance.save()

        if delete_data:
            # User 객체 삭제 시 외래키 참조 데이터도 자동으로 삭제됩니다.
            instance.delete()
            # instance는 삭제되었으므로, 이 시점 이후 instance에 접근하면 오류 발생 가능
            # 뷰에서 응답을 반환하기 전에 delete()가 호출되므로, 뷰에서 메시지를 구성해야 합니다.

        return instance
