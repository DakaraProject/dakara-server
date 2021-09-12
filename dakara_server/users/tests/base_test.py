from django.conf import settings
from django.test import override_settings

from internal.tests.base_test import BaseAPITestCase, BaseProvider


class UsersProvider(BaseProvider):
    """Provides helper function for users tests."""


class UsersAPITestCase(BaseAPITestCase, UsersProvider):
    """Base users test class for Unittest."""


def config_email_disabled(func):
    """Modify config to simulate no email verification."""

    def caller(*args, **kwargs):
        rest_registration = settings.REST_REGISTRATION.copy()
        rest_registration["REGISTER_VERIFICATION_ENABLED"] = False
        rest_registration["REGISTER_EMAIL_VERIFICATION_ENABLED"] = False
        rest_registration["RESET_PASSWORD_VERIFICATION_ENABLED"] = False

        return override_settings(
            EMAIL_ENABLED=False, REST_REGISTRATION=rest_registration
        )(func)(*args, **kwargs)

    return caller
