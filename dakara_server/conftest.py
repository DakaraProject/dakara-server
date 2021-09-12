import os

import django

# We manually designate which settings we will be using in an environment variable
# This is similar to what occurs in the `manage.py`
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dakara_server.settings.test")


def pytest_configure():
    django.setup()
