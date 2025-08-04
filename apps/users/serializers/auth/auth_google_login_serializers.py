from rest_framework import serializers


class GoogleLoginSerializer(serializers.Serializer[dict[str, str]]):
    code = serializers.CharField(help_text="구글 OAuth2 authorization code")


class GoogleLoginResponseSerializer(serializers.Serializer[dict[str, str]]):
    status = serializers.CharField()
    message = serializers.CharField()
    user = serializers.DictField()
    access_token = serializers.CharField()
    refresh_token = serializers.CharField()
