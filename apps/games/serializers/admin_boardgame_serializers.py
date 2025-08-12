from typing import Any, cast

from django.db import InternalError
from rest_framework import serializers

from apps.games.models import Category, Game, GameGenre, Genre


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


# 관리자 보드 게임 수정 API
class AdminGameUpdateSerializer(serializers.ModelSerializer[Game]):

    id = serializers.IntegerField(source="game_id", read_only=True, help_text="등록된 보드 게임의 고유 ID")
    title = serializers.CharField(max_length=255, help_text="보드 게임의 고유한 이름")
    age = serializers.IntegerField(help_text="게임의 권장 연령")
    description = serializers.CharField(required=False, allow_blank=True, help_text="보드 게임 상세 설명")

    min_players = serializers.IntegerField(required=False, help_text="최소 플레이어 수")
    max_players = serializers.IntegerField(required=False, help_text="최대 플레이어 수")
    playtime_min_minutes = serializers.IntegerField(required=False, help_text="최소 플레이 시간 (분)")
    playtime_max_minutes = serializers.IntegerField(required=False, help_text="최대 플레이 시간 (분)")

    difficulty = serializers.FloatField(required=False, help_text="난이도 (0~5 스케일)")

    image_url = serializers.URLField(
        source="thumbnail_url", required=False, allow_blank=True, help_text="대표 이미지 URL"
    )
    rules_url = serializers.URLField(required=False, allow_blank=True, help_text="게임 규칙 파일 URL")

    # 응답 필드 (읽기 전용) - 명세서에 맞춰 필드명 유지
    like_count = serializers.IntegerField(read_only=True, help_text="좋아요 수")
    reviews_count = serializers.IntegerField(read_only=True, help_text="리뷰 개수")
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
            "reviews_count",
            "created_at",
            "updated_at",
        ]

    def validate_title(self, value: str) -> str:

        if self.instance:
            current_game_instance = cast(Game, self.instance)
            if Game.objects.filter(title=value).exclude(pk=current_game_instance.pk).exists():
                raise serializers.ValidationError("이미 동일한 이름의 보드 게임이 등록되어 있습니다.")
        elif Game.objects.filter(title=value).exists():
            raise serializers.ValidationError("이미 동일한 이름의 보드 게임이 등록되어 있습니다.")
        return value

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:

        # min_players가 max_players보다 크지 않도록 교차 필드 유효성 검사
        min_players = data.get("min_players", getattr(self.instance, "min_players", None))
        max_players = data.get("max_players", getattr(self.instance, "max_players", None))

        if min_players is not None and max_players is not None and min_players > max_players:
            raise serializers.ValidationError({"min_players": "'min_players'는 'max_players'보다 클 수 없습니다."})

        return data

    def update(self, instance: Game, validated_data: dict[str, Any]) -> Game:

        return super().update(instance, validated_data)


# 게임-장르 관계 생성을 위한 시리얼라이저입니다.
class AdminGameGenreSerializer(serializers.ModelSerializer[GameGenre]):

    # 게임 ID와 장르 ID를 받아 관계를 설정합니다.
    game_id = serializers.IntegerField(write_only=True, help_text="장르를 연결할 게임의 고유 ID")
    genre_id = serializers.IntegerField(write_only=True, help_text="게임에 연결할 장르의 고유 ID")

    game_title = serializers.CharField(source="game.title", read_only=True, help_text="연결된 게임의 이름")
    genre_name = serializers.CharField(source="genre.name", read_only=True, help_text="연결된 장르의 이름")

    class Meta:
        model = GameGenre
        fields = ["id", "game_id", "genre_id", "game_title", "genre_name", "created_at"]
        read_only_fields = ["id", "game_title", "genre_name", "created_at"]
        extra_kwargs = {
            "game_id": {"required": True},
            "genre_id": {"required": True},
        }

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:

        # 게임과 장르가 실제로 존재하는지, 그리고 이미 관계가 존재하는지 검증합니다.
        game_id_raw = data.get("game_id")
        genre_id_raw = data.get("genre_id")

        game_id = cast(int, game_id_raw)
        genre_id = cast(int, genre_id_raw)

        try:
            game_instance = Game.objects.get(game_id=game_id)
        except Game.DoesNotExist:
            raise serializers.ValidationError({"game_id": "해당 ID의 게임을 찾을 수 없습니다."})

        try:
            genre_instance = Genre.objects.get(genre_id=genre_id)
        except Genre.DoesNotExist:
            raise serializers.ValidationError({"genre_id": "해당 ID의 장르를 찾을 수 없습니다."})

        # 이미 관계가 존재하는지 확인
        if GameGenre.objects.filter(game=game_instance, genre=genre_instance).exists():
            raise serializers.ValidationError("해당 게임과 장르는 이미 연결되어 있습니다.")

        data["game"] = game_instance
        data["genre"] = genre_instance
        return data

    def create(self, validated_data: dict[str, Any]) -> GameGenre:

        # GameGenre 인스턴스를 생성합니다.
        game = validated_data.pop("game")
        genre = validated_data.pop("genre")
        return GameGenre.objects.create(game=game, genre=genre)
