from .base import *

# 테스트 전용 설정

DEBUG = True
TESTING = True

STATIC_URL = "/static/"
MEDIA_URL = "/media/"

# STATICFILES_STORAGE: S3 대신 로컬 사용
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"

# DEFAULT_FILE_STORAGE: media 파일도 S3 안 쓰게 설정
DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"

# 이메일 전송 없이 메모리 내에서만 처리
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# 비밀번호 검증 속도 빠르게
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]
