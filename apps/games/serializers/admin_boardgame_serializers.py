import logging  # 로깅을 위해 임포트
import os  # 파일 확장자를 얻기 위해 os 모듈 임포트
import uuid
from typing import Any, cast

from django.core.files.uploadedfile import UploadedFile
from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

# 이 경로는 실제 Django 프로젝트 구조에 맞게 조정해야 합니다.
from apps.games.models import Category, Game, GameCategory, GameGenre, Genre

# S3Uploader 임포트 (사용자님이 제공해주신 파일에서)
from core.utils.s3_file_upload import S3Uploader

logger = logging.getLogger(__name__)


# 관리자 보드게임 등록
class AdminGameRegisterSerializer(serializers.ModelSerializer[Game]):

    id = serializers.IntegerField(source="game_id", read_only=True, help_text="등록된 보드 게임의 고유 ID")
    title = serializers.CharField(max_length=255, help_text="보드 게임의 고유한 이름")
    age = serializers.IntegerField(help_text="게임의 권장 연령")
    description = serializers.CharField(required=False, allow_blank=True, help_text="보드 게임 상세 설명")

    categories = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), many=True, required=False, help_text="카테고리 ID 목록 (예: [1, 3])"
    )
    genres = serializers.PrimaryKeyRelatedField(
        queryset=Genre.objects.all(),
        many=True,  # <--- many=True 설정은 여러 값을 기대합니다.
        required=False,
        help_text="장르 ID 목록 (예: [1, 2])",
    )

    min_players = serializers.IntegerField(help_text="최소 플레이어 수")
    max_players = serializers.IntegerField(help_text="최대 플레이어 수")
    playtime_min_minutes = serializers.IntegerField(help_text="최소 플레이 시간 (분)")
    playtime_max_minutes = serializers.IntegerField(help_text="최대 플레이 시간 (분)")
    difficulty = serializers.FloatField(help_text="난이도 (0~5 스케일)")

    thumbnail_url = serializers.URLField(max_length=255, read_only=True, help_text="S3에 저장된 썸네일 이미지 URL")
    thumbnail_file = serializers.ImageField(
        required=False, allow_null=True, write_only=True, help_text="업로드할 이미지 파일 (JPG/PNG 등)"
    )

    rules_url = serializers.URLField(
        max_length=255, required=False, allow_blank=True, help_text="게임 규칙 파일 URL"
    )  # <--- URLField는 유효한 URL 형식을 기대합니다.

    like_count = serializers.IntegerField(read_only=True, help_text="좋아요 수")
    reviewsCount = serializers.IntegerField(source="reviews_count", read_only=True, help_text="리뷰 개수")

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
            "categories",
            "genres",
            "min_players",
            "max_players",
            "playtime_min_minutes",
            "playtime_max_minutes",
            "difficulty",
            "thumbnail_url",
            "thumbnail_file",
            "rules_url",
            "like_count",
            "reviewsCount",
            "created_at",
            "updated_at",
        ]
        extra_kwargs = {
            "title": {"required": True},
            "age": {"required": True},
            "min_players": {"required": True},
            "max_players": {"required": True},
            "playtime_min_minutes": {"required": True},
            "playtime_max_minutes": {"required": True},
            "difficulty": {"required": True},
        }

    def validate_title(self, value: str) -> str:
        if self.instance is None and Game.objects.filter(title=value).exists():
            raise serializers.ValidationError("이미 동일한 이름의 보드 게임이 등록되어 있습니다.")
        return value

    def create(self, validated_data: dict[str, Any]) -> Game:
        categories_objects = validated_data.pop("categories", [])
        genres_objects = validated_data.pop("genres", [])
        thumbnail_file = validated_data.pop("thumbnail_file", None)

        s3_uploader = S3Uploader()
        uploaded_s3_key_for_rollback = None

        try:
            with transaction.atomic():
                game_instance = super().create(validated_data)

                if thumbnail_file:
                    file_extension = os.path.splitext(thumbnail_file.name)[1] or ".jpg"
                    unique_name = f"{uuid.uuid4().hex[:6]}_{game_instance.pk}{file_extension}"
                    s3_key = f"game_thumbnails/{unique_name}"

                    thumbnail_s3_url = s3_uploader.upload_file(file_obj=thumbnail_file, s3_key=s3_key)

                    if thumbnail_s3_url:
                        game_instance.thumbnail_url = thumbnail_s3_url
                        game_instance.save(update_fields=["thumbnail_url"])
                        uploaded_s3_key_for_rollback = s3_key
                    else:
                        logger.error(f"S3 썸네일 이미지 업로드 실패: {thumbnail_file.name}")
                        raise serializers.ValidationError({"detail": "썸네일 이미지 업로드에 실패했습니다."})

                if categories_objects:
                    game_category_instances = [
                        GameCategory(game=game_instance, category=category_obj) for category_obj in categories_objects
                    ]
                    GameCategory.objects.bulk_create(game_category_instances)

                if genres_objects:
                    game_genre_instances = [
                        GameGenre(game=game_instance, genre=genre_obj) for genre_obj in genres_objects
                    ]
                    GameGenre.objects.bulk_create(game_genre_instances)

            return game_instance

        except Exception as e:
            if uploaded_s3_key_for_rollback:
                try:
                    s3_uploader.delete_file(uploaded_s3_key_for_rollback)
                    logger.info(f"S3 롤백 성공: {uploaded_s3_key_for_rollback}")
                except Exception as delete_err:
                    logger.error(f"S3 롤백 실패: {uploaded_s3_key_for_rollback}, 오류: {delete_err}")

            if game_instance and game_instance.pk:
                game_instance.delete()
                logger.info(f"게임 롤백 성공: {game_instance.title}")

            logger.exception("게임 등록 처리 중 오류 발생")
            if isinstance(e, serializers.ValidationError):
                raise e
            raise serializers.ValidationError({"detail": f"게임 등록 처리 중 오류가 발생했습니다: {str(e)}"})


# 관리자 보드게임 수정
class AdminGameUpdateSerializer(serializers.ModelSerializer[Game]):

    categories = serializers.SlugRelatedField(
        many=True, read_only=False, slug_field="category_id", queryset=Category.objects.all(), required=False
    )

    genres = serializers.SlugRelatedField(
        many=True, read_only=False, slug_field="genre_id", queryset=Genre.objects.all(), required=False
    )

    thumbnail_file = serializers.ImageField(write_only=True, required=False)

    class Meta:
        model = Game
        fields = [
            "game_id",
            "title",
            "age",
            "description",
            "categories",
            "genres",
            "min_players",
            "max_players",
            "playtime_min_minutes",
            "playtime_max_minutes",
            "difficulty",
            "thumbnail_file",
            "rules_url",
            "thumbnail_url",
            "like_count",
            "reviews_count",
            "average_rating",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["game_id", "like_count", "reviews_count", "average_rating", "created_at", "updated_at"]

    #  데이터 유효성 검사 및 비즈니스 로직 검증을 수행합니다.
    def validate(self, data: dict[str, Any]) -> dict[str, Any]:

        # self.instance가 Game 객체일 경우, MyPy에게 이 시점에서 Game 타입임을 알려줍니다.
        game_instance: Game | None = None
        if self.instance:
            game_instance = cast(Game, self.instance)

        # min_players와 max_players 유효성 검사
        # 요청 데이터에 없으면 기존 인스턴스 값을 사용하고, 인스턴스가 없으면 None을 사용합니다.
        min_players = data.get("min_players", game_instance.min_players if game_instance else None)
        max_players = data.get("max_players", game_instance.max_players if game_instance else None)

        if min_players is not None and max_players is not None and min_players > max_players:
            raise ValidationError(
                {"error": "VALIDATION_ERROR", "message": "'min_players'는 'max_players'보다 클 수 없습니다."}
            )

        # title 중복 검사
        new_title = data.get("title", None)
        # 새로운 title이 제공되었고, 기존 인스턴스가 있으며, 새로운 title이 기존 title과 다를 때만 중복 검사
        if new_title is not None and game_instance and new_title != game_instance.title:
            if Game.objects.filter(title=new_title).exists():
                raise ValidationError(
                    {"error": "DUPLICATE_TITLE", "message": "입력된 게임 이름과 동일한 보드 게임이 이미 존재합니다."}
                )

        return data

    # 유효성 검사를 통과한 데이터를 사용하여 Game 인스턴스를 업데이트
    def update(self, instance: Game, validated_data: dict[str, Any]) -> Game:
        categories_data = validated_data.pop("categories", None)
        genres_data = validated_data.pop("genres", None)
        thumbnail_file = validated_data.pop("thumbnail_file", None)

        s3_uploader = S3Uploader()  # 임포트한 S3Uploader 인스턴스 생성
        uploaded_s3_url_for_rollback = None  # S3Uploader의 delete_file은 URL을 받으므로 키 대신 URL 저장

        try:
            with transaction.atomic():
                for attr, value in validated_data.items():
                    setattr(instance, attr, value)

                if thumbnail_file:
                    file_extension = os.path.splitext(thumbnail_file.name)[1] or ".jpg"
                    unique_name = f"{uuid.uuid4().hex[:6]}_{instance.game_id}{file_extension}"
                    s3_key = f"game_thumbnails/{unique_name}"  # S3 내 저장 경로

                    old_thumbnail_url = instance.thumbnail_url
                    if old_thumbnail_url:
                        # 기존 S3Uploader의 delete_file 메서드는 URL을 직접 받습니다.
                        s3_uploader.delete_file(old_thumbnail_url)

                    thumbnail_s3_url = s3_uploader.upload_file(file_obj=thumbnail_file, s3_key=s3_key)

                    if thumbnail_s3_url:
                        instance.thumbnail_url = thumbnail_s3_url  # 새로운 S3 URL 저장
                        uploaded_s3_url_for_rollback = thumbnail_s3_url  # 롤백을 위해 URL 저장
                    else:
                        logger.error(f"S3 썸네일 이미지 업로드 실패: {thumbnail_file.name}")
                        raise serializers.ValidationError({"detail": "썸네일 이미지 업로드에 실패했습니다."})

                if categories_data is not None:
                    instance.categories.set(categories_data)

                if genres_data is not None:
                    instance.genres.set(genres_data)

                instance.save()

            return instance

        except Exception as e:
            if uploaded_s3_url_for_rollback:
                logger.warning(f"트랜잭션 실패로 인해 S3 파일 롤백: {uploaded_s3_url_for_rollback}")
                s3_uploader.delete_file(uploaded_s3_url_for_rollback)  # URL로 삭제

            raise e
