"""
Django test settings for the Dakara server project.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.11/ref/settings/

This file should not be modified if you are not a dev.
"""

import os

from dakara_server.settings.base import *  # noqa F403

# use test config
SECRET_KEY = "test secret key"
DEBUG = True
ALLOWED_HOSTS = ["*"]

# use sqlite database
DATABASES = {"default": {"NAME": os.devnull, "ENGINE": "django.db.backends.sqlite3"}}

# use memory channels backend
CHANNEL_LAYERS = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}

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
