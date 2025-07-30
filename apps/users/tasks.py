import logging
from datetime import date

from celery import shared_task  # type: ignore # mypy 오류 해결을 위해 추가
from celery.app.task import Task  # type: ignore # mypy 오류 해결을 위해 추가
from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)  # type: ignore # mypy 오류 해결을 위해 추가
def send_verification_email_task(self: Task, email: str, code: str) -> None:
    try:
        send_mail(
            subject="이메일 인증 코드입니다.",
            message=f"인증 코드는 {code} 입니다.",
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[email],
            fail_silently=False,
        )
    except Exception as exception:
        logger.warning(f"[재시도] 이메일 전송 실패: {email}/사유: {exception}")
        raise self.retry(exc=exception)
