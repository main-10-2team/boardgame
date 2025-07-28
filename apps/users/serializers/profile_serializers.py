from rest_framework import serializers

from apps.users.models import User


class UserProfileSerializer(serializers.ModelSerializer[User]):
    preferred_genres = serializers.SerializerMethodField()
    preferred_playtimes = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()
    like_count = serializers.SerializerMethodField()

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
