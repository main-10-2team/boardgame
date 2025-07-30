from rest_framework import serializers

from apps.games.models import Game, Review
from apps.users.models import User


class ReviewSerializer(serializers.ModelSerializer[Review]):

    id = serializers.IntegerField(source="review_id", read_only=True)
    gameId = serializers.IntegerField(source="game.game_id", read_only=True)
    userId = serializers.IntegerField(source="user.id", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)
    rating = serializers.FloatField(read_only=True)
    content = serializers.CharField(read_only=True)

    createdAt = serializers.DateTimeField(source="created_at", format="%Y-%m-%d %H:%M:%S", read_only=True)
    updatedAt = serializers.DateTimeField(source="updated_at", format="%Y-%m-%d %H:%M:%S", read_only=True)

    status = serializers.CharField(read_only=True)

    class Meta:
        model = Review

        fields = ["id", "gameId", "userId", "username", "rating", "content", "createdAt", "updatedAt", "status"]

        read_only_fields = fields
