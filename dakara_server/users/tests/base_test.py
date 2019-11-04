from internal.tests.base_test import BaseAPITestCase, BaseProvider


class UsersProvider(BaseProvider):
    """Provides helper function for users tests
    """


class UsersAPITestCase(BaseAPITestCase, UsersProvider):
    """Base users test class for Unittest
    """
