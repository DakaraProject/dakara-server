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
from dj_database_url import parse as db_url

from dakara_server.settings.base import *  # noqa F403

SECRET_KEY = config("SECRET_KEY", default="secret_key")
DEBUG = config("DEBUG", cast=bool, default=False)
ALLOWED_HOSTS = config("ALLOWED_HOSTS", cast=Csv(), default="[]")
CSRF_TRUSTED_ORIGINS = ["http://localhost"]

# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases
# `DATABASE_URL` is specified according to dj-databse-url plugin
# https://github.com/kennethreitz/dj-database-url#url-schema

DATABASES = {
    "default": config(
        "DATABASE_URL", cast=db_url, default="mysql://dakara:dakara@mysql/dakara"
    )
}

# Channels
# http://channels.readthedocs.io/en/latest/topics/channel_layers.html

CHANNEL_LAYERS = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}

# Static root
# Should point to the static directory served by nginx
STATIC_ROOT = config("STATIC_ROOT", "/app/static")

# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = config("LANGUAGE", default="en-us")

TIME_ZONE = config("TIME_ZONE", default="UTC")

# Loggin config
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "[%(asctime)s] [%(process)d] %(levelname)s %(message)s",
            "datefmt": "[%Y-%m-%d %H:%M:%S %z]",
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
            "filename": config("LOG_FILE_PATH", default="/data/logs/dakara_server.log"),
            "maxBytes": config("LOG_FILE_MAX_SIZE", cast=int, default=1000000),
            "backupCount": config("LOG_FILE_BACKUP_COUNT", cast=int, default=2),
            "formatter": "default",
        },
    },
    "loggers": {
        "playlist.views": {"handlers": ["logfile"], "level": "INFO"},
        "playlist.date_stop": {"handlers": ["logfile"], "level": "INFO"},
        "playlist.consumers": {"handlers": ["logfile"], "level": "INFO"},
        "playlist.management.commands.runapscheduler": {
            "handlers": ["logfile"],
            "level": "INFO",
        },
        "django": {
            "handlers": ["logfile"],
            "level": config("DJANGO_LOG_LEVEL", default="INFO"),
        },
    },
}

# email backend
EMAIL_HOST = config("EMAIL_HOST", default="postfix")
EMAIL_PORT = config("EMAIL_PORT", cast=int, default="25")
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = config("EMAIL_USE_TLS", cast=bool, default="false")
EMAIL_USE_SSL = config("EMAIL_USE_SSL", cast=bool, default="false")
EMAIL_TIMEOUT = config("EMAIL_TIMEOUT", cast=int, default="0") or None
EMAIL_SSL_KEYFILE = config("EMAIL_SSL_KEYFILE", default="") or None
EMAIL_SSL_CERTIFICATE = config("EMAIL_SSL_CERTIFICATE", default="") or None

# values imported from base config
# SENDER_EMAIL is get from the environment
# HOST_URL is get from the environment
