import pytest


@pytest.fixture
def library_provider():
    from library.tests.base_test import LibraryProvider

    provider = LibraryProvider()
    provider.create_test_data()
    return provider
