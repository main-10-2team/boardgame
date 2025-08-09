from datetime import datetime
from typing import Dict
from datetime import timedelta
from django.utils import timezone

from apps.users.models import User

# 유저 하나 생성
def create_test_user(
    *,
    email: str = "test@example.com",
    password: str = "password123",
    name: str = "테스터",
    nickname: str = "tester",
    phone_number: str = "01012345678",
    birth: datetime = datetime(2000, 1, 1),
    profile_image: str = "",
    review_count: int = 0,
    like_count: int = 0,
    role: str = "user",
    status: str = "active",
    suspended_until: datetime | None = None,
) -> User:
    user = User.objects.create_user(
        email=email,
        password=password,
        name=name,
        nickname=nickname,
        phone_number=phone_number,
        birth=birth,
        profile_image=profile_image,
    )
    user.review_count = review_count
    user.like_count = like_count
    user.role = role
    user.status = status
    user.suspended_until = suspended_until
    user.save()
    return user

# 테스트용 유저 4개 생성
def create_all_user_types() -> Dict[str, User]:

    return {
        "normal_user": create_test_user(
            email="normal@example.com",
            password="normalpass123",
            name="일반 사용자",
            nickname="normaluser",
            phone_number="01012345678",
            birth=datetime(1995, 5, 15),
            profile_image="https://example.com/images/normal.png",
            review_count=2,
            like_count=5,
            role="user",
            status="active",
        ),
        "admin_user": create_test_user(
            email="admin@example.com",
            password="adminpass123",
            name="관리자",
            nickname="adminuser",
            phone_number="01011112222",
            birth=datetime(1990, 1, 1),
            profile_image="https://example.com/images/admin.png",
            review_count=10,
            like_count=20,
            role="admin",
            status="active",
        ),
        "suspended_user": create_test_user(
            email="suspended@example.com",
            password="suspended123",
            name="제재 유저",
            nickname="suspendeduser",
            phone_number="01033334444",
            birth=datetime(1998, 8, 8),
            profile_image="https://example.com/images/suspended.png",
            review_count=1,
            like_count=0,
            role="user",
            status="suspended",
            suspended_until=timezone.now() + timedelta(days=30),
        ),
        "deleted_user": create_test_user(
            email="deleted@example.com",
            password="deleted123",
            name="탈퇴 유저",
            nickname="deleteduser",
            phone_number="01055556666",
            birth=datetime(1992, 2, 2),
            profile_image="https://example.com/images/deleted.png",
            review_count=0,
            like_count=0,
            role="user",
            status="deleted",
            suspended_until=None,
        )
    }