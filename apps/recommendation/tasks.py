from celery import shared_task
from django.core.management import call_command
import logging

logger = logging.getLogger(__name__)


@shared_task
def run_sync_games_to_redis():

    try:
        logger.info("Celery Beat: 매일 Redis 게임 데이터 동기화를 시작합니다.")


        call_command('games_to_redis')

        logger.info("Celery Beat: 매일 Redis 게임 데이터 동기화가 성공적으로 완료되었습니다.")

    except Exception as e:
        logger.error(f"Celery Beat: 매일 동기화 작업 중 오류가 발생했습니다: {e}", exc_info=True)