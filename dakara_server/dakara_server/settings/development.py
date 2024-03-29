"""
Django local settings for the Dakara server project.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.2/ref/settings/

You should not modify this file directly.
To modify config values, set them as environment variables,
or in a config file in the dakara root directory:
either in a `.env` file
or in a `settings.ini` with a single `[settings]` section.
"""

import os

from decouple import config
from dj_database_url import parse as db_url

os.environ.setdefault("HOST_URL", "http://localhost:3000")

from dakara_server.settings.base import *  # noqa F403
from dakara_server.settings.base import BASE_DIR  # noqa E402

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.2/howto/deployment/checklist/

SECRET_KEY = "YourSecretKey"
DEBUG = True
ALLOWED_HOSTS = ["*"]

# Django password security policy
# https://docs.djangoproject.com/en/2.2/topics/auth/passwords/#module-django.contrib.auth.password_validation

AUTH_PASSWORD_VALIDATORS = []

# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases
# `DATABASE_URL` is specified according to dj-databse-url plugin
# https://github.com/kennethreitz/dj-database-url#url-schema

DATABASES = {
    "default": db_url("sqlite:///" + os.path.join(BASE_DIR, "db.sqlite3")),
}

# Channels
# http://channels.readthedocs.io/en/latest/topics/channel_layers.html

CHANNEL_LAYERS = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}

# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

# Loggin config
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {"format": "[%(asctime)s] %(levelname)s %(message)s"},
        "no_time": {"format": "%(levelname)s %(message)s"},
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
        "console_playlist": {"class": "logging.StreamHandler", "formatter": "default"},
        "console_interactive": {
            "class": "logging.StreamHandler",
            "formatter": "no_time",
        },
    },
    "loggers": {
        "playlist.views": {"handlers": ["console_playlist"], "level": "INFO"},
        "playlist.date_stop": {"handlers": ["console_playlist"], "level": "INFO"},
        "playlist.consumers": {"handlers": ["console_playlist"], "level": "INFO"},
        "library.management.commands.feed": {
            "handlers": ["console_interactive"],
            "level": "INFO",
        },
        "library.management.commands.createworks": {
            "handlers": ["console_interactive"],
            "level": "INFO",
        },
        "django": {
            "handlers": ["console"],
            "level": config("DJANGO_LOG_LEVEL", default="INFO"),
        },
    },
}

# email backend
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# values imported from base config
# SENDER_EMAIL is get from the environment
# HOST_URL is get from the environment
