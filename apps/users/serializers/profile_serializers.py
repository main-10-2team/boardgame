from rest_framework import serializers

from apps.users.models import User


class UserProfileSerializer(serializers.ModelSerializer[User]):
    user_id = serializers.IntegerField(source="id")

    class Meta:
        model = User
        fields = [
            "user_id",
            "email",
            "nickname",
            "birth",
            "phone_number",
            "role",
            "status",
            "created_at",
            "updated_at",
        ]

        read_only_fields = fields
