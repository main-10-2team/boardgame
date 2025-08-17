import logging
import os
from typing import Any, Optional, Set, cast  # Optional과 cast 임포트

import numpy as np
from django_redis import get_redis_connection  # type: ignore
from redis import Redis  # Redis 클라이언트의 타입을 명시적으로 임포트
from redis.commands.search.query import Query

logger = logging.getLogger(__name__)

# 회원가입 용 redis 함수


# 이메일 인증 코드를 Redis에 저장. 시간은 5분
def store_signup_email_code(email: str, code: str) -> None:
    redis: Redis = get_redis_connection("default")
    redis.set(f"signup:email:{email}", code, ex=300)


# redis 에서 이메일 인증 코드 조회
def get_signup_email_code(email: str) -> str | None:
    redis: Redis = get_redis_connection("default")
    code_bytes_raw = redis.get(f"signup:email:{email}")
    # mypy가 Awaitable[Any]로 잘못 추론하는 것을 방지하기 위해 명시적으로 캐스팅
    code_bytes = cast(Optional[bytes], code_bytes_raw)
    return code_bytes.decode("utf-8") if code_bytes else None


# 이메일 인증 성공 시 인증 완료 상태를 Redis에 저장, 유효시간은 1시간 으로 설정
def mark_signup_email_as_verified(email: str) -> None:
    redis: Redis = get_redis_connection("default")
    redis.set(f"signup:email:verified:{email}", "true", ex=3600)


# 이메일 인증 여부 확인
def is_signup_email_verified(email: str) -> bool:
    redis: Redis = get_redis_connection("default")
    result = redis.get(f"signup:email:verified:{email}")
    # mypy 오류 해결을 위해 None 체크를 명시적으로 추가
    return result == b"true" if result is not None else False


# 인증 코드 삭제
def delete_signup_email_code(email: str) -> None:
    redis: Redis = get_redis_connection("default")
    redis.delete(f"signup:email:{email}")


# 탈퇴 복구 용 redis 함수


# 이메일 인증 코드를 Redis에 저장. 시간은 5분.
def store_restore_email_code(email: str, code: str) -> None:
    redis: Redis = get_redis_connection("default")
    key = f"restore:email:{email}"
    redis.set(key, code, ex=300)


# redis 에서 이메일 인증 코드 조회.
def get_restore_email_code(email: str) -> str | None:
    redis: Redis = get_redis_connection("default")
    key = f"restore:email:{email}"
    code_bytes_raw = redis.get(key)
    # mypy가 Awaitable[Any]로 잘못 추론하는 것을 방지하기 위해 명시적으로 캐스팅
    code_bytes = cast(Optional[bytes], code_bytes_raw)
    return code_bytes.decode("utf-8") if code_bytes else None


# 이메일 인증 성공 시 인증 완료 상태를 Redis에 저장, 유효시간은 1시간 으로 설정.
def mark_restore_email_as_verified(email: str) -> None:
    redis: Redis = get_redis_connection("default")
    redis.set(f"restore:email:verified:{email}", "true", ex=3600)


# 이메일 인증 여부 확인.
def is_restore_email_verified(email: str) -> bool:
    redis: Redis = get_redis_connection("default")
    result = redis.get(f"restore:email:verified:{email}")
    # mypy 오류 해결을 위해 None 체크를 명시적으로 추가
    return result == b"true" if result is not None else False


# 인증 코드 삭제
def delete_restore_email_code(email: str) -> None:
    redis: Redis = get_redis_connection("default")
    redis.delete(f"restore:email:{email}")


# 휴대폰 인증 완료 표시 (기본 TTL 5분)
def mark_phone_verified(phone: str, ttl: int = 300) -> None:
    redis: Redis = get_redis_connection("default")
    redis.set(f"phone_verified:{phone}", "true", ex=ttl)


# 휴대폰 인증 여부 확인
def is_phone_verified(phone: str) -> bool:
    redis: Redis = get_redis_connection("default")
    result = redis.get(f"phone_verified:{phone}")
    # mypy 오류 해결을 위해 None 체크를 명시적으로 추가
    return result == b"true" if result is not None else False


# 비밀번호 찾기용


# 이메일 인증 코드를 Redis에 저장. 시간은 5분
def store_reset_email_code(email: str, code: str) -> None:
    redis: Redis = get_redis_connection("default")
    redis.set(f"reset:email:{email}", code, ex=300)


# redis 에서 이메일 인증 코드 조회
def get_reset_email_code(email: str) -> str | None:
    redis: Redis = get_redis_connection("default")
    code_bytes_raw = redis.get(f"reset:email:{email}")
    # mypy가 Awaitable[Any]로 잘못 추론하는 것을 방지하기 위해 명시적으로 캐스팅
    code_bytes = cast(Optional[bytes], code_bytes_raw)
    return code_bytes.decode("utf-8") if code_bytes else None


# 이메일 인증 성공 시 인증 완료 상태를 Redis에 저장, 유효시간은 1시간 으로 설정
def mark_reset_email_as_verified(email: str) -> None:
    redis: Redis = get_redis_connection("default")
    redis.set(f"reset:email:verified:{email}", "true", ex=3600)


# 이메일 인증 여부 확인
def is_reset_email_verified(email: str) -> bool:
    redis: Redis = get_redis_connection("default")
    result = redis.get(f"reset:email:verified:{email}")
    # mypy 오류 해결을 위해 None 체크를 명시적으로 추가
    return result == b"true" if result is not None else False


# 인증 코드 삭제
def delete_reset_email_code(email: str) -> None:
    redis: Redis = get_redis_connection("default")
    redis.delete(f"reset:email:{email}")


# 이메일 찾기 위한 휴대폰 인증
# 휴대폰 인증 완료 표시 (기본 TTL 5분)
def mark_email_find_phone_as_verified(phone: str, ttl: int = 300) -> None:
    redis: Redis = get_redis_connection("default")
    redis.set(f"email_find:verified:{phone}", "true", ex=ttl)


# 휴대폰 인증 여부 확인
def is_email_find_phone_verified(phone: str) -> bool:
    redis: Redis = get_redis_connection("default")
    result = redis.get(f"email_find:verified:{phone}")
    # mypy 오류 해결을 위해 None 체크를 명시적으로 추가
    return result == b"true" if result is not None else False
