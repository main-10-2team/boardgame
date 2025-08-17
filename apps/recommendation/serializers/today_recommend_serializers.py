from typing import Any

from rest_framework import serializers

from apps.recommendation.constants.today_constants import QUESTIONS_DATA


class GameQuestionStepSerializer(serializers.Serializer[Any]):
    step = serializers.IntegerField()

    def validate_step(self, value: int) -> int:

        if value not in QUESTIONS_DATA:
            raise serializers.ValidationError("유효하지 않은 질문 단계입니다. 1에서 5 사이의 값만 사용할 수 있습니다.")
        return value
