from typing import Any, Dict, List, cast
from django.db.models import F
from rest_framework import serializers

from apps.games.models import Game, Like
from apps.users.models import User


class SurveyGameSerializer(serializers.Serializer[Dict[str, Any]]):
    game_id = serializers.IntegerField()
    title = serializers.CharField()
    thumbnail_url = serializers.URLField()
    average_rating = serializers.FloatField()


class SurveyChoiceResponseSerializer(serializers.Serializer[Dict[str, Any]]):
    games = SurveyGameSerializer(many=True)


class SurveySubmitSerializer(serializers.Serializer[Dict[str, Any]]):
    liked_games = serializers.ListField(child=serializers.IntegerField(min_value=1), allow_empty=True)

    def validate_liked_games(self, value: List[int]) -> List[int]:
        if not value:
            return value

        if len(value) != len(set(value)):
            raise serializers.ValidationError({"detail": "중복된 게임 ID가 포함되어 있습니다."})

        survey_ids = set(value)
        valid_ids = set(Game.objects.filter(game_id__in=survey_ids).values_list("game_id", flat=True))

        invalid_ids = survey_ids - valid_ids
        if invalid_ids:
            raise serializers.ValidationError({"detail": f"존재하지 않는 게임 ID - {sorted(invalid_ids)}"})

        return list(survey_ids)

    def save(self, **kwargs: Any) -> Dict[str, Any]:
        user = cast(User, kwargs.get("user"))
        liked_ids = self.validated_data["liked_games"]
        if not liked_ids:
            return {
                "new_like_count": 0,
                "liked_game_ids": [],
            }

        existing_liked_ids = set(Like.objects.filter(user=user).values_list("game__game_id", flat=True))

        new_game_ids = list(set(liked_ids) - existing_liked_ids)

        if not new_game_ids:
            return {"new_like_count": 0, "liked_game_ids": []}

        valid_games = Game.objects.filter(game_id__in=new_game_ids)
        new_likes_count = valid_games.count()

        Like.objects.bulk_create([Like(user=user, game=game) for game in valid_games], ignore_conflicts=True)
        valid_games.update(like_count=F("like_count") + 1)
        User.objects.filter(pk=user.pk).update(like_count=F("like_count") + new_likes_count)

        return {
            "new_like_count": new_likes_count,
            "liked_game_ids": new_game_ids,
        }
