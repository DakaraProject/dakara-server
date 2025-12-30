"""
Django test settings for the Dakara server project.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.2/ref/settings/

This file should not be modified if you are not a dev.
"""

import os

from dakara_server.settings.base import *  # noqa F403
from dakara_server.settings.base import (
    EMAIL_ENABLED,
    get_host_urls,
    get_rest_registration,
)

# use test config
HOST_URL = "http://frontend-host"
SENDER_EMAIL = "no-reply@frontend-host"
SECRET_KEY = "test secret key"
DEBUG = True
ALLOWED_HOSTS = ["*"]

# use sqlite database
DATABASES = {"default": {"NAME": os.devnull, "ENGINE": "django.db.backends.sqlite3"}}

# use memory channels backend
CHANNEL_LAYERS = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}

# use memory cache
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "TIMEOUT": None,
    }
}

# use faster password hasher
PASSWORD_HASHERS = ("django.contrib.auth.hashers.MD5PasswordHasher",)

# use default localization settings
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"

# enable extended logging
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
        "django": {"handlers": ["console"], "level": "INFO"},
    },
}

PLAYLIST_SIZE_LIMIT = 100

EMAIL_BACKEND = "django.core.mail.backends.dummy.EmailBackend"

REST_REGISTRATION = get_rest_registration(HOST_URL, SENDER_EMAIL, EMAIL_ENABLED)
HOST_URLS = get_host_urls(HOST_URL)
