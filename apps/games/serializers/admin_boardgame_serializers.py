from typing import Any

from django.db import InternalError
from rest_framework import serializers

from apps.games.models import Category, Game, Genre


# 관리자 보드 게임 등록 API를 위한 시리얼라이저입니다.
class AdminGameRegisterSerializer(serializers.ModelSerializer[Game]):

    # Game 모델과 연동하여 데이터를 직렬화하고 유효성을 검사합니다.

    id = serializers.IntegerField(source="game_id", read_only=True, help_text="등록된 보드 게임의 고유 ID")
    title = serializers.CharField(max_length=255, help_text="보드 게임의 고유한 이름")
    age = serializers.IntegerField(help_text="게임의 권장 연령")
    description = serializers.CharField(required=False, allow_blank=True, help_text="보드 게임 상세 설명")

    min_players = serializers.IntegerField(required=False, help_text="최소 플레이어 수")
    max_players = serializers.IntegerField(required=False, help_text="최대 플레이어 수")
    playtime_min_minutes = serializers.IntegerField(required=False, help_text="최소 플레이 시간 (분)")
    playtime_max_minutes = serializers.IntegerField(required=False, help_text="최대 플레이 시간 (분)")

    # **[수정됨]** difficulty를 FloatField로 변경
    difficulty = serializers.FloatField(required=False, help_text="난이도 (0~5 스케일)")

    # **[추가됨]** image_url 및 rules_url 필드 정의
    image_url = serializers.URLField(
        source="thumbnail_url", required=False, allow_blank=True, help_text="대표 이미지 URL"
    )
    rules_url = serializers.URLField(required=False, allow_blank=True, help_text="게임 규칙 파일 URL")

    # **[수정됨]** reviewsCount 필드명을 명세에 맞춰 like_count와 일관되게 조정
    like_count = serializers.IntegerField(read_only=True, help_text="좋아요 수")
    reviewsCount = serializers.IntegerField(
        source="reviews_count", read_only=True, help_text="리뷰 개수"
    )  # **[수정됨]** source 추가

    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True, help_text="정보 생성일시")
    updated_at = serializers.DateTimeField(
        format="%Y-%m-%d %H:%M:%S", read_only=True, help_text="정보 최종 업데이트 일시"
    )

    class Meta:
        model = Game
        fields = [
            "id",
            "title",
            "age",
            "description",
            "min_players",
            "max_players",
            "playtime_min_minutes",
            "playtime_max_minutes",
            "difficulty",
            "image_url",
            "rules_url",
            "like_count",
            "reviewsCount",
            "created_at",
            "updated_at",
        ]

        extra_kwargs = {
            "title": {"required": True},
            "age": {"required": True},
        }

    def validate_title(self, value: str) -> str:

        # 게임 타이틀의 고유성을 검사합니다.
        if self.instance is None and Game.objects.filter(title=value).exists():
            raise serializers.ValidationError("이미 동일한 이름의 보드 게임이 등록되어 있습니다.")
        return value

    # 유효성 검사가 완료된 데이터로 Game 인스턴스를 생성합니다.
    def create(self, validated_data: dict[str, Any]) -> Game:

        # ModelSerializer는 source가 지정된 필드와 모델 필드명이 일치하는 필드를 자동으로 매핑합니다.
        return super().create(validated_data)
