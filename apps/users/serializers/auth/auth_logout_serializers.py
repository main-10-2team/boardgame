from rest_framework import serializers


class LogoutSerializer(serializers.Serializer):# type: ignore
    refresh_token = serializers.CharField(help_text="JWT 리프레시 토큰", write_only=True)


class LogoutResponseSerializer(serializers.Serializer):# type: ignore
    status = serializers.CharField()
    message = serializers.CharField()
