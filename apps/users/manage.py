from typing import TYPE_CHECKING, Any

from django.contrib.auth.base_user import BaseUserManager

if TYPE_CHECKING:
    from apps.users.models import User


class CustomUserManager(BaseUserManager["User"]):
    def create_user(self, email: str, password: str, **extra_fields: Any) -> "User":
        if not email:
            raise ValueError("이메일은 필수입니다.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        # is_staff와 is_superuser 대신 role 필드만 'admin'으로 설정합니다.
        extra_fields.setdefault('role', 'admin')

        # role이 'admin'이 아니면 에러를 발생시킵니다.
        if extra_fields.get('role') != 'admin':
            raise ValueError('Superuser must have role="admin".')

        # is_staff와 is_superuser는 @property로 정의되었으므로,
        # 이 필드를 직접 전달하지 않고 role만 설정하면 됩니다.
        return self.create_user(email, password, **extra_fields)
