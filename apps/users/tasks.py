import logging

from celery import shared_task  # type: ignore # mypy 오류 해결을 위해 추가
from celery.app.task import Task  # type: ignore # mypy 오류 해결을 위해 추가
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from apps.users.models import AccountDeletionReason

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


# 정기 실행되어 삭제 예정일이 지난 유저들 삭제
def clean_up_due_deletions() -> None:

    now = timezone.now()
    count = 0

    reasons = AccountDeletionReason.objects.filter(
        due_date__lte=now,
        user__isnull=False,
        user__status="deleted",
    ).select_related("user")

    for reason in reasons:
        user = reason.user
        if user:
            try:
                user.delete()
                count += 1
                logger.info(f"[정리 삭제] 유저 {user.user_id} 삭제 완료 (due_date: {reason.due_date})")
            except Exception as e:
                logger.error(f"[정리 삭제] 유저 {user.user_id} 삭제 실패: {e}")

    logger.info(f"[정리 삭제] 총 {count}명 삭제 완료.")
