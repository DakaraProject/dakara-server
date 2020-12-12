"""
Django base settings for the Dakara server project.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.11/ref/settings/

This file should not be modified if you are not a dev.
"""

import os

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

ASGI_APPLICATION = "dakara_server.routing.application"

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
}


SENDER_EMAIL = "no-reply@example.com"


# Django rest registration config
REST_REGISTRATION = {
    "LOGIN_AUTHENTICATE_SESSION": False,
    "LOGIN_SERIALIZER_CLASS": "users.serializers.DakaraLoginSerializer",
    "REGISTER_VERIFICATION_URL": "https://frontend-host/verify-user/",
    "RESET_PASSWORD_VERIFICATION_URL": "https://frontend-host/reset-password/",
    "REGISTER_EMAIL_VERIFICATION_URL": "https://frontend-host/verify-email/",
    "VERIFICATION_FROM_EMAIL": SENDER_EMAIL,
    "USER_VERIFICATION_FLAG_FIELD": "validated_by_email",
    "USER_LOGIN_FIELDS": ["username", "email"],
}

AUTHENTICATION_BACKENDS = ["users.backend.DakaraModelBackend"]


HOST_URLS = {"NOTIFICATION_TO_MANAGERS_URL": "https://frontend-host/settings/users"}
