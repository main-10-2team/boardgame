from rest_framework import serializers

from apps.games.models import Game, Review
from apps.users.models import User


class ReviewSerializer(serializers.ModelSerializer[Review]):

    # id = serializers.IntegerField(source="review_id", read_only=True)
    # game_id = serializers.IntegerField(source="game.game_id", read_only=True)
    # user_id = serializers.IntegerField(source="user.user_id", read_only=True)
    username = serializers.CharField(source="user.nickname", read_only=True)
    # rating = serializers.FloatField(read_only=True)
    # content = serializers.CharField(read_only=True)
    #
    # created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
    # updated_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)

    status = serializers.BooleanField(read_only=True)


    class Meta:
        model = Review

        fields = ["review_id", "game_id", "user_id", "username", "rating", "content", "created_at", "updated_at", "status"]

        read_only_fields = fields
