from typing import Any, Optional, cast

from django.db.models.fields.files import ImageFieldFile
from django.views.decorators.csrf import csrf_exempt
from rest_framework import serializers

from apps.users.models import User


class EmailLoginSerializer(serializers.Serializer[Any]):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class EmailLoginResponseSerializer(serializers.ModelSerializer[Any]):
    profile_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "user_id",
            "email",
            "nickname",
            "phone_number",
            "birth",
            "role",
            "status",
            "profile_url",
        )

    def get_profile_url(self, obj: User) -> Optional[str]:
        profile_image = obj.profile_image
        if isinstance(profile_image, ImageFieldFile) and profile_image.name:
            return str(profile_image.url)
        return None
