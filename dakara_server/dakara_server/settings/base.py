"""
Django base settings for the Dakara server project.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.11/ref/settings/

This file should not be modified if you are not a dev.
"""

import os

from decouple import config

from dakara_server.version import __version__ as VERSION, __date__ as DATE  # noqa F401


BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Application definition

INSTALLED_APPS = (
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework.authtoken",
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

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "TIMEOUT": None,
    }
}

WSGI_APPLICATION = "dakara_server.wsgi.application"


# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/

STATIC_URL = "/static/"

STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]

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
    "DEFAULT_SCHEMA_CLASS": "rest_framework.schemas.coreapi.AutoSchema",
}


SENDER_EMAIL = config("SENDER_EMAIL", default="no-reply@example.com")
HOST_URL = config("HOST_URL")
EMAIL_ENABLED = config("EMAIL_ENABLED", default=True, cast=bool)


# Django rest registration config
REST_REGISTRATION = {
    "LOGIN_AUTHENTICATE_SESSION": False,
    "LOGIN_SERIALIZER_CLASS": "users.serializers.DakaraLoginSerializer",
    "REGISTER_VERIFICATION_URL": HOST_URL + "/verify-registration/",
    "RESET_PASSWORD_VERIFICATION_URL": HOST_URL + "/reset-password/",
    "REGISTER_EMAIL_VERIFICATION_URL": HOST_URL + "/verify-email/",
    "VERIFICATION_FROM_EMAIL": SENDER_EMAIL,
    "USER_VERIFICATION_FLAG_FIELD": "validated_by_email",
    "USER_LOGIN_FIELDS": ["username", "email"],
    "REGISTER_VERIFICATION_ENABLED": EMAIL_ENABLED,
    "REGISTER_EMAIL_VERIFICATION_ENABLED": EMAIL_ENABLED,
    "RESET_PASSWORD_VERIFICATION_ENABLED": EMAIL_ENABLED,
}

AUTHENTICATION_BACKENDS = ["users.backends.DakaraModelBackend"]


# Front URLs
HOST_URLS = {
    "USER_EDIT_URL": HOST_URL + "/settings/users/{id}",
    "LOGIN_URL": HOST_URL + "/login",
}

# limit of the playlist size
PLAYLIST_SIZE_LIMIT = config("PLAYLIST_SIZE_LIMIT", cast=int, default=100)
