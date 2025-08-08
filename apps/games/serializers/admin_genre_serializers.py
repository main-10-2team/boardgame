from typing import cast

from rest_framework import serializers

from apps.games.models import Genre


class AdminGenreCreateSerializer(serializers.ModelSerializer[Genre]):  # [Genre] 추가
    id = serializers.IntegerField(source="gener_id", read_only=True, help_text="등록된 장르의 고유 아이디")
    name = serializers.CharField(max_length=255, help_text="등록된 장르의 이름")

    class Meta:
        model = Genre
        fields = ["id", "name"]
        read_only_fields = ["id"]


class AdminGenreUpdateSerializer(serializers.ModelSerializer[Genre]):
    id = serializers.IntegerField(source="gener_id", read_only=True, help_text="수정된 장르의 고유 ID")
    name = serializers.CharField(max_length=255, help_text="변경된 장르의 이름")

    class Meta:
        model = Genre
        fields = ["id", "name"]
        read_only_fields = ["id"]  # ID는 읽기 전용

    def validate_name(self, value: str) -> str:
        # 현재 인스턴스(업데이트 대상 장르)를 제외하고 동일한 이름이 있는지 확인
        if self.instance:
            current_genre = cast(Genre, self.instance)
            if Genre.objects.filter(name=value).exclude(genre_id=current_genre.genre_id).exists():
                raise serializers.ValidationError("이미 동일한 이름의 장르가 존재합니다.")
        elif not self.instance and Genre.objects.filter(name=value).exists():  # 생성 시에도 중복 체크 (방어적 코딩)
            raise serializers.ValidationError("이미 동일한 이름의 장르가 존재합니다.")
        return value


# 관리자 장르 목록 조회 API를 위한 시리얼라이저입니다.
class AdminGenreListSerializer(serializers.ModelSerializer[Genre]):

    # 장르의 ID, 이름, 생성일시, 수정일시를 직렬화합니다.
    id = serializers.IntegerField(source="genre_id", read_only=True)

    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
    updated_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)

    class Meta:
        model = Genre
        fields = ["id", "name", "created_at", "updated_at"]
        read_only_fields = fields
