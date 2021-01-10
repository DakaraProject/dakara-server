import pytest


@pytest.fixture
def users_provider():
    from users.tests.base_test import UsersProvider

    provider = UsersProvider()
    provider.create_test_data()
    return provider
