from rest_framework import serializers

from apps.games.models import Genre


class AdminGenreCreateSerializer(serializers.ModelSerializer[Genre]):  # [Genre] 추가
    id = serializers.IntegerField(source="gener_id", read_only=True, help_text="등록된 장르의 고유 아이디")
    name = serializers.CharField(max_length=255, help_text="등록된 장르의 이름")

    class Meta:
        model = Genre
        fields = ["id", "name"]
        read_only_fields = ["id"]
