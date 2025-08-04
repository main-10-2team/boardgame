from rest_framework import serializers
from apps.users.models import User


# 관리자 회원 정보 조회
class UserSerializer(serializers.ModelSerializer):


    # API 명세서의 "id" 필드는 User 모델의 "user_id"에 해당합니다.
    id = serializers.IntegerField(source='user_id', read_only=True)

    # API 명세서의 "username" 필드는 User 모델의 "nickname"에 해당합니다.
    username = serializers.CharField(source='nickname', read_only=True)

    email = serializers.EmailField(read_only=True)

    created_at = serializers.DateTimeField(read_only=True, format="%Y-%m-%d %H:%M:%S")

    # Django의 AbstractBaseUser에 기본적으로 포함된 last_login 필드를 사용합니다.
    last_login = serializers.DateTimeField(read_only=True, format="%Y-%m-%d %H:%M:%S")

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'created_at', 'last_login')



