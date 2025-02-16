import pytest


@pytest.fixture
def users_provider():
    from users.tests.base_test import UsersProvider

    provider = UsersProvider()
    provider.create_test_data()
    return provider


@pytest.fixture
def config_email_disabled(settings):
    rest_registration = settings.REST_REGISTRATION.copy()
    rest_registration["REGISTER_VERIFICATION_ENABLED"] = False
    rest_registration["REGISTER_EMAIL_VERIFICATION_ENABLED"] = False
    rest_registration["RESET_PASSWORD_VERIFICATION_ENABLED"] = False

    settings.EMAIL_ENABLED = False
    settings.REST_REGISTRATION = rest_registration
