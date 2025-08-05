from typing import Any, Dict, List

from rest_framework import serializers

from apps.games.models import Game, Like


class LikeSerializer(serializers.Serializer[Dict[str, Any]]):
    """
    좋아요 API의 요청 본문을 처리하는 시리얼라이저입니다.
    """

    game_id = serializers.IntegerField(required=True, help_text="좋아요를 추가/취소할 게임의 고유 아이디")

    def validate_game_id(self, value: int) -> int:
        """
        제공된 game_id가 유효한지 검증합니다.
        """
        if not Game.objects.filter(game_id=value).exists():
            raise serializers.ValidationError("유효하지 않은 게임 ID 입니다.")
        return value


class LikeResponseSerializer(serializers.Serializer[Dict[str, Any]]):
    """
    좋아요 API의 성공 응답 본문을 처리하는 시리얼라이저입니다.
    """

    status = serializers.CharField(default="success", help_text="요청 처리 상태")
    action = serializers.CharField(help_text="수행된 동작 ('added' 또는 'removed')")
    game_id = serializers.IntegerField(help_text="좋아요가 적용된 게임의 ID")
    user_id = serializers.IntegerField(help_text="좋아요를 요청한 사용자의 ID")
    total_likes = serializers.IntegerField(help_text="해당 게임의 총 좋아요 수")


class LikedGameSerializer(serializers.Serializer[Dict[str, Any]]):
    """
    좋아요 목록 조회 API에서 좋아요를 누른 게임 각각의 상세 정보를 나타내는 시리얼라이저입니다.
    """

    game_id = serializers.IntegerField(source="game.game_id", help_text="게임의 고유 ID")
    title = serializers.CharField(source="game.title", help_text="게임 제목")
    image_url = serializers.URLField(source="game.thumbnail_url", help_text="게임 이미지 URL")
    average_rating = serializers.FloatField(source="game.average_rating", help_text="게임 평균 평점")
    created_at = serializers.DateTimeField(help_text="좋아요 추가일 (ISO 8601 형식)")


class LikeListResponseSerializer(serializers.Serializer[Dict[str, Any]]):
    """
    좋아요 목록 조회 API의 성공 응답 전체를 처리하는 시리얼라이저입니다.
    """

    status = serializers.CharField(default="success", help_text="요청 처리 상태")
    user_like_count = serializers.IntegerField(help_text="좋아요를 누른 게임 수")
    likes = LikedGameSerializer(many=True, help_text="좋아요를 누른 게임 목록")
