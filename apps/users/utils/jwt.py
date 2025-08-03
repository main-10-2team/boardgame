from datetime import timedelta
from typing import Tuple

from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.models import User  # User 모델을 임포트합니다.


def generate_jwt_token_pair(user: User) -> Tuple[str, str]:
    refresh = RefreshToken.for_user(user)
    refresh.set_exp(lifetime=timedelta(days=7))  # 예: refresh 7일
    refresh.access_token.set_exp(lifetime=timedelta(minutes=40))  # 예: access 40분
    return str(refresh.access_token), str(refresh)
