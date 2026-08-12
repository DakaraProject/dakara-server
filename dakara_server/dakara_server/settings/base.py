"""
Django base settings for the Dakara server project.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.1/ref/settings/

This file should not be modified if you are not a dev.
"""

from pathlib import Path

from decouple import config

from dakara_server.version import __date__ as DATE  # noqa F401
from dakara_server.version import __version__ as VERSION  # noqa F401

BASE_DIR = Path(__file__).resolve().parent.parent.parent
PROJECT_DIR = BASE_DIR.parent


# Application definition

INSTALLED_APPS = (
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "daphne",
    "django.contrib.staticfiles",
    "django_apscheduler",
    "rest_framework",
    "rest_framework.authtoken",
    "drf_spectacular",
    "channels",
    "ordered_model",
    "rest_registration",
    "library",
    "playlist.apps.PlaylistConfig",
    "users.apps.UsersConfig",
    "internal.apps.InternalConfig",
)

MIDDLEWARE = (
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
)

# user model

AUTH_USER_MODEL = "users.DakaraUser"

# channels

ASGI_APPLICATION = "dakara_server.asgi.application"

# fields

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# urls

ROOT_URLCONF = "dakara_server.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]


WSGI_APPLICATION = "dakara_server.wsgi.application"


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = "/static/"

# Django REST config
REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.TokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_PAGINATION_CLASS": "internal.pagination.PageNumberPaginationCustom",
    "PAGE_SIZE": 10,
    "TEST_REQUEST_DEFAULT_FORMAT": "json",
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

# DRF Spectacular settings
SPECTACULAR_SETTINGS = {
    "TITLE": "Dakara server API",
    "DESCRIPTION": "Server for the Dakara project",
    "VERSION": VERSION,
    "SERVE_INCLUDE_SCHEMA": False,
}


EMAIL_ENABLED = config("DAKARA_EMAIL_ENABLED", default=True, cast=bool)


# Django rest registration config
def get_rest_registration(host_url, sender_email, email_enabled):
    return {
        "LOGIN_AUTHENTICATE_SESSION": False,
        "LOGIN_SERIALIZER_CLASS": "users.serializers.DakaraLoginSerializer",
        "REGISTER_VERIFICATION_URL": host_url + "/verify-registration/",
        "RESET_PASSWORD_VERIFICATION_URL": host_url + "/reset-password/",
        "REGISTER_EMAIL_VERIFICATION_URL": host_url + "/verify-email/",
        "VERIFICATION_FROM_EMAIL": sender_email,
        "USER_VERIFICATION_FLAG_FIELD": "validated_by_email",
        "USER_LOGIN_FIELDS": ["username", "email"],
        "REGISTER_VERIFICATION_ENABLED": email_enabled,
        "REGISTER_EMAIL_VERIFICATION_ENABLED": email_enabled,
        "RESET_PASSWORD_VERIFICATION_ENABLED": email_enabled,
    }


AUTHENTICATION_BACKENDS = ["users.backends.DakaraModelBackend"]


# Front URLs
def get_host_urls(host_url):
    return {
        "USER_EDIT_URL": host_url + "/settings/users/{id}",
        "LOGIN_URL": host_url + "/login",
    }


# limit of the playlist size
PLAYLIST_SIZE_LIMIT = config("DAKARA_PLAYLIST_SIZE_LIMIT", cast=int, default=1000)

# interval of the scheduler (in minutes)
SCHEDULER_INTERVAL = config("DAKARA_SCHEDULER_INTERVAL", cast=int, default=5)
