import os

from celery import Celery  # type: ignore
from celery.schedules import crontab  # type: ignore

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

app = Celery("boardq")

app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
app.conf.beat_schedule = {
    "daily-user-deletion-cleanup": {
        "task": "apps.users.tasks.clean_up_due_deletions",
        "schedule": crontab(minute=0, hour=3),
    },
    "sync-games-to-redis-weekly": {
        "task": "apps.recommendation.tasks.tasks.run_sync_games_to_redis",
        "schedule": crontab(minute=0, hour=4, day_of_week="mon"),
    },
    "update-feature-bounds-daily": {
        "task": "apps.recommendation.tasks.tasks.run_update_feature_bounds",
        "schedule": crontab(minute=30, hour=3),
    },
}
