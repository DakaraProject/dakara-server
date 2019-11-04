from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase


UserModel = get_user_model()
tz = timezone.get_default_timezone()


class BaseProvider:
    """Provides helper functions for tests
    """

    @staticmethod
    def authenticate(user, client=None, headers=None):
        """Authenticate and set the token to the given client

        Args:
            user (users.models.DakaraUser): user to authenticate.
            client (rest_framework.test.APIClient): HTTP client. If given, the
                token of the user authenticated is integrated to it.
            headers (list): list of headers. If given, the token is added as a
                tuple.
        """
        token, _ = Token.objects.get_or_create(user=user)

        if client is not None:
            client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        if headers is not None:
            headers.append((b"authorization", "Token {}".format(token.key).encode()))

    @staticmethod
    def create_user(
        username, playlist_level=None, library_level=None, users_level=None, **kwargs
    ):
        """Create a user with the given permissions

        Args:
            username (str): name of the user.
            playlist_level (str): level of accreditation for playlist app.
            library_level (str): level of accreditation for library app.
            users_level (str): level of accreditation for users app.

        Returns:
            users.models.DakaraUser: created user.
        """
        user = UserModel.objects.create_user(username, "", "password", **kwargs)
        user.playlist_permission_level = playlist_level
        user.library_permission_level = library_level
        user.users_permission_level = users_level
        user.save()
        return user


class BaseAPITestCase(APITestCase, BaseProvider):
    """Base test class for Unittest
    """

    def authenticate(self, user):
        """Authenticate using the embedded client

        Args:
            user (users.models.DakaraUser): user to authenticate.
        """
        super().authenticate(user, client=self.client)
