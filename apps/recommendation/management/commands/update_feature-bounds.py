import logging
from typing import Any

from django.core.cache import cache
from django.core.management.base import BaseCommand
from django.db.models import Max, Min

from apps.games.models import Game

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "게임 데이터의 수치형 특성(min/max)을 계산하여 캐시에 저장합니다."

    def handle(self, *args: Any, **options: Any) -> None:
        self.stdout.write(self.style.SUCCESS("수치형 특성 범위 계산을 시작합니다."))
        logger.info("수치형 특성 범위 계산 및 캐싱 작업을 시작합니다.")
        try:
            bounds = Game.objects.aggregate(
                min_age=Min("age"),
                max_age=Max("age"),
                min_players=Min("min_players"),
                max_players=Max("max_players"),
                min_playtime=Min("playtime_min_minutes"),
                max_playtime=Max("playtime_max_minutes"),
                min_difficulty=Min("difficulty"),
                max_difficulty=Max("difficulty"),
            )

            feature_bounds = {
                "age": (bounds["min_age"] or 3, bounds["max_age"] or 20),
                "players": (bounds["min_players"] or 1, bounds["max_players"] or 10),
                "playtime": (bounds["min_playtime"] or 10, bounds["max_playtime"] or 999),
                "difficulty": (bounds["min_difficulty"] or 1.0, bounds["max_difficulty"] or 5.0),
            }

            cache.set("numerical_feature_bounds", feature_bounds, timeout=None)

            self.stdout.write(self.style.SUCCESS("성공적으로 캐시에 저장했습니다."))
            logger.info(f"계산된 특성 범위를 캐시에 저장했습니다: {feature_bounds}")
        except Exception:
            self.stdout.write(self.style.ERROR("통계치 계산 중 오류가 발생했습니다. 로그를 확인해주세요."))
            logger.critical("통계치 계산 및 캐싱 중 예상치 못한 오류가 발생했습니다.", exc_info=True)
