from django.db.models import Count
from rest_framework import serializers

from apps.games.models import Genre
from apps.users.models import User


class UserProfileSerializer(serializers.ModelSerializer[User]):
    preferred_genres = serializers.SerializerMethodField()
    preferred_playtimes = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()
    like_count = serializers.SerializerMethodField()
    popular_genres = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "name",
            "email",
            "nickname",
            "profile_image",
            "review_count",
            "like_count",
            "created_at",
            "preferred_genres",
            "preferred_playtimes",
            "popular_genres",
        ]

        read_only_fields = fields

    def get_review_count(self, obj: User) -> int:
        return obj.reviews.all().count()

    def get_like_count(self, obj: User) -> int:
        return obj.likes.all().count()

    def get_preferred_genres(self, obj: User) -> list[str]:
        return [genre.name for genre in obj.preferred_genres.all()]

    def get_preferred_playtimes(self, obj: User) -> list[str]:
        return [pt.name for pt in obj.preferred_playtimes.all()]

    def get_popular_genres(self, obj: User) -> list[str]:
        genre_qs = (
            Genre.objects.filter(genre_games__game__liked_by_users__user=obj)
            .annotate(like_count=Count("genre_games__game__liked_by_users"))
            .order_by("-like_count")[:10]
        )

        if not genre_qs.exists():
            return []

        return [genre.name for genre in genre_qs]
