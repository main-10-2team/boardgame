from config.settings.base import *

DEBUG = False
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + OWNER_APPS
INSTALLED_APPS.remove("debug_toolbar")

MIDDLEWARE = [m for m in MIDDLEWARE if "debug_toolbar" not in m]

# Static files (CSS, JavaScript, Images)
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "static"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

INTERNAL_IPS = [
    "127.0.0.1",
]

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}