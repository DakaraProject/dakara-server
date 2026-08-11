"""
Django local settings for the Dakara server project.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.1/ref/settings/

You should not modify this file directly. To modify config values, set them as
environment variables, or in a config file in the current worknig directory:
either in a `.env` file or in a `settings.ini` with a single `[settings]`
section.

If you want to customize this file more, duplicate it under a different name.
"""

from decouple import Csv, config
from dj_database_url import config as config_db
from dj_database_url import register
from dj_email_url import config as config_email

from dakara_server.settings.base import *  # noqa F403
from dakara_server.settings.base import (
    EMAIL_ENABLED,
    PROJECT_DIR,
    get_host_urls,
    get_rest_registration,
)

SENDER_EMAIL = config("DAKARA_SENDER_EMAIL", default="no-reply@example.com")
HOST_URL = config("DAKARA_HOST_URL", default="http://example.com")
SECRET_KEY = config("DAKARA_SECRET_KEY", default="secret_key")
DEBUG = config("DAKARA_DEBUG", cast=bool, default=False)
ALLOWED_HOSTS = config("DAKARA_ALLOWED_HOSTS", cast=Csv(), default="")
CSRF_TRUSTED_ORIGINS = [
    HOST_URL,
    *config("DAKARA_CSRF_TRUSTED_ORIGINS", cast=Csv(), default=""),
]

# register mysql-connector for database URL
register("mysql-connector", "mysql.connector.django")

# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases
# `DAKARA_DATABASE_URL` is specified according to dj-databse-url plugin
# https://github.com/kennethreitz/dj-database-url#url-schema

DATABASES = {
    "default": config_db(
        "DAKARA_DATABASE_URL",
        default="mysql-connector://user:password@mysql:3306/dakara",
    )
}

REDIS_URL = config("DAKARA_REDIS_URL", default="redis://cache:6379")

# Channels
# http://channels.readthedocs.io/en/latest/topics/channel_layers.html

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [
                {
                    "address": REDIS_URL,
                    # prevent TimeoutError of Redis
                    # see: https://github.com/redis/redis-py/issues/4091#issuecomment-4576644995
                    # TODO remove this for future version of Redis
                    "socket_timeout": None,
                }
            ]
        },
    }
}

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": f"{REDIS_URL}/1",
        "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
    }
}

SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"

# Static files for production only
# Should point to the static directory served by nginx
STATIC_ROOT = config("DAKARA_STATIC_ROOT", default=PROJECT_DIR / "static")

# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = config("DAKARA_LANGUAGE_CODE", default="en-us")

TIME_ZONE = config("DAKARA_TIME_ZONE", default="UTC")

if config("DAKARA_LOG_TO_CONSOLE", cast=bool, default=False):
    log_handlers = ["console_interactive"]
else:
    log_handlers = ["logfile"]

# Loggin config
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "[%(asctime)s] [%(process)d] %(levelname)s %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S %z",
        },
    },
    "filters": {
        "require_debug_false": {"()": "django.utils.log.RequireDebugFalse"},
        "require_debug_true": {"()": "django.utils.log.RequireDebugTrue"},
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "filters": ["require_debug_true"],
        },
        "console_interactive": {
            "class": "logging.StreamHandler",
            "formatter": "default",
        },
        "logfile": {
            "level": "DEBUG",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": config(
                "DAKARA_LOG_FILE_PATH", default="/data/logs/dakara_server.log"
            ),
            "maxBytes": config("DAKARA_LOG_FILE_MAX_SIZE", cast=int, default=1000000),
            "backupCount": config("DAKARA_LOG_FILE_BACKUP_COUNT", cast=int, default=2),
            "formatter": "default",
        },
    },
    "loggers": {
        "playlist.views": {
            "handlers": log_handlers,
            "level": config("DAKARA_LOG_LEVEL", default="INFO"),
        },
        "playlist.date_stop": {
            "handlers": log_handlers,
            "level": config("DAKARA_LOG_LEVEL", default="INFO"),
        },
        "playlist.consumers": {
            "handlers": log_handlers,
            "level": config("DAKARA_LOG_LEVEL", default="INFO"),
        },
        "playlist.management.commands.runapscheduler": {
            "handlers": log_handlers,
            "level": config("DAKARA_LOG_LEVEL", default="INFO"),
        },
        "django": {
            "handlers": log_handlers,
            "level": config("DJANGO_LOG_LEVEL", default="INFO"),
        },
    },
}

# email backend
EMAIL = config_email("DAKARA_EMAIL_URL", default="smtp://user:password@postfix:25")
EMAIL_HOST = EMAIL["EMAIL_HOST"]
EMAIL_PORT = EMAIL["EMAIL_PORT"]
EMAIL_HOST_USER = EMAIL["EMAIL_HOST_USER"]
EMAIL_HOST_PASSWORD = EMAIL["EMAIL_HOST_PASSWORD"]
EMAIL_USE_TLS = EMAIL["EMAIL_USE_TLS"]
EMAIL_USE_SSL = EMAIL["EMAIL_USE_SSL"]
EMAIL_TIMEOUT = EMAIL["EMAIL_TIMEOUT"]
EMAIL_SSL_KEYFILE = config("DAKARA_EMAIL_SSL_KEYFILE", default=None)
EMAIL_SSL_CERTIFICATE = config("DAKARA_EMAIL_SSL_CERTIFICATE", default=None)

REST_REGISTRATION = get_rest_registration(HOST_URL, SENDER_EMAIL, EMAIL_ENABLED)
HOST_URLS = get_host_urls(HOST_URL)
