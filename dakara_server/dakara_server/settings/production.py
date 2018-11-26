"""
Django local settings for the Dakara server project.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.11/ref/settings/

This file is aimed to be used for production use. For local use, see
'local.py'/'local_example.py'.

To modify this file, copy it to 'production.py'.
"""

import os
from warnings import warn

from .base import *  # noqa F403
from .base import BASE_DIR

SECRET_KEY = 'YourSecretKey'
DEBUG = False
ALLOWED_HOSTS = ['www.example.com']

# Django password security policy
# https://docs.djangoproject.com/en/1.11/topics/auth/passwords/#module-django.contrib.auth.password_validation
# AUTH_PASSWORD_VALIDATORS = []

# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Channels
# http://channels.readthedocs.io/en/latest/topics/channel_layers.html

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    },
}

# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

# Loggin config
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': '[%(asctime)s] %(levelname)s %(message)s'
        },
        'no_time': {
            'format': '%(levelname)s %(message)s'
        }
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'default',
            'filters': ['require_debug_true'],
        },
        'console_playlist': {
            'class': 'logging.StreamHandler',
            'formatter': 'default',
        },
        'console_interactive': {
            'class': 'logging.StreamHandler',
            'formatter': 'no_time',
        },
    },
    'loggers': {
        'playlist.views': {
            'handlers': ['console_playlist'],
            'level': 'INFO',
        },
        'playlist.consumers': {
            'handlers': ['console_playlist'],
            'level': 'INFO',
        },
        'library.management.commands.feed': {
            'handlers': ['console_interactive'],
            'level': 'INFO',
        },
        'library.management.commands.createworks': {
            'handlers': ['console_interactive'],
            'level': 'INFO',
        },
        'django': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
        },
    },
}

# limit of the playlist size
PLAYLIST_SIZE_LIMIT = 100

# import local production settings
try:
    from .development_local import *  # noqa F403

except ImportError:
    warn("You are currently using the default production config file. "
         "You should create the file 'production_local.py' in "
         "'dakara_server/dakara_server/settings' to edit its values.")
