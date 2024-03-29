from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

UserModel = get_user_model()
tz = timezone.get_default_timezone()


class BaseProvider:
    """Provides helper functions for tests."""

    @staticmethod
    def authenticate(user, client=None, headers=None):
        """Authenticate and set the token to the given client.

        Args:
            user (users.models.DakaraUser): User to authenticate.
            client (rest_framework.test.APIClient): HTTP client. If given, the
                token of the user authenticated is integrated to it.
            headers (list): List of headers. If given, the token is added as a
                tuple.
        """
        token, _ = Token.objects.get_or_create(user=user)

        if client is not None:
            client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        if headers is not None:
            headers.append((b"authorization", "Token {}".format(token.key).encode()))

    @staticmethod
    def create_user(
        username,
        email=None,
        password="password",
        playlist_level=None,
        library_level=None,
        users_level=None,
        **kwargs
    ):
        """Create a user with the given permissions.

        Extra arguments are passed to `UserModel.objects.create_user`.

        Args:
            username (str): Name of the user.
            email (str): Email of the user.
            password (str): Password of the user.
            playlist_level (str): Level of accreditation for playlist app.
            library_level (str): Level of accreditation for library app.
            users_level (str): Level of accreditation for users app.

        Returns:
            users.models.DakaraUser: Created user.
        """
        if email is None:
            email = "{}@example.com".format(username)

        user = UserModel.objects.create_user(username, email, password, **kwargs)
        user.playlist_permission_level = playlist_level
        user.library_permission_level = library_level
        user.users_permission_level = users_level
        user.validated_by_email = True
        user.validated_by_manager = True
        user.save()
        return user


class BaseAPITestCase(APITestCase, BaseProvider):
    """Base test class for Unittest."""

    def authenticate(self, user):
        """Authenticate using the embedded client

        Args:
            user (users.models.DakaraUser): User to authenticate.
        """
        super().authenticate(user, client=self.client)
