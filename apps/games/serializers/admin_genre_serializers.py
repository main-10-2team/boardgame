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
            # **[수정됨]** self.instance를 Genre 타입으로 명시적으로 캐스팅
            current_genre = cast(Genre, self.instance)
            if Genre.objects.filter(name=value).exclude(genre_id=current_genre.genre_id).exists():
                raise serializers.ValidationError("이미 동일한 이름의 장르가 존재합니다.")
        elif not self.instance and Genre.objects.filter(name=value).exists():  # 생성 시에도 중복 체크 (방어적 코딩)
            raise serializers.ValidationError("이미 동일한 이름의 장르가 존재합니다.")
        return value
