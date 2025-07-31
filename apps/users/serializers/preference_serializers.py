from rest_framework import serializers

from apps.games.models import Genre, PlaytimeCategory


class PreferenceSubmitSerializer(serializers.Serializer[dict[str, object]]):
    genres = serializers.ListField(
        child=serializers.IntegerField(min_value=1), allow_empty=False, help_text="선호 장르 ID 목록"
    )
    playtimes = serializers.ListField(
        child=serializers.IntegerField(min_value=1), allow_empty=False, help_text="선호 플레이타임 카테고리 ID 목록"
    )

    def validate_genres(self, value: list[int]) -> list[int]:
        invalid_ids = set(value) - set(Genre.objects.filter(pk__in=value).values_list("pk", flat=True))
        if invalid_ids:
            raise serializers.ValidationError("유효하지 않은 장르입니다.")
        return value

    def validate_playtimes(self, value: list[int]) -> list[int]:
        invalid_ids = set(value) - set(PlaytimeCategory.objects.filter(pk__in=value).values_list("pk", flat=True))
        if invalid_ids:
            raise serializers.ValidationError("유효하지 않은 플레이타임 ID가 포함되어 있습니다.")
        return value
