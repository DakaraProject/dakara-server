from unittest.mock import MagicMock

from django.core.exceptions import ValidationError

from users.backends import DakaraModelBackend
from users.tests.base_test import UsersAPITestCase, config_email_disabled


class DakaraModelBackendTestCase(UsersAPITestCase):
    """Test the authentication backend."""

    def setUp(self):
        # create a user without any rights
        self.user = self.create_user("TestUser", email="test@user.com", password="pass")

    def test_authenticate_username_superuser(self):
        """Test to authenticate as superuser."""
        self.user.is_superuser = True
        self.user.validated_by_email = False
        self.user.validated_by_manager = False
        self.user.save()

        backend = DakaraModelBackend()
        self.assertEqual(
            backend.authenticate(MagicMock(), username="TestUser", password="pass"),
            self.user,
        )

    def test_authenticate_username_not_active(self):
        """Test to authenticate an inactive user."""
        self.user.is_active = False
        self.user.save()

        backend = DakaraModelBackend()
        self.assertIsNone(
            backend.authenticate(MagicMock(), username="TestUser", password="pass"),
        )

    def test_authenticate_username_not_validated_by_email(self):
        """Test to authenticate when not validated by email."""
        self.user.validated_by_email = False
        self.user.validated_by_manager = True
        self.user.save()

        backend = DakaraModelBackend()
        with self.assertRaisesRegex(
            ValidationError, "This user email has not been validated"
        ):
            backend.authenticate(MagicMock(), username="TestUser", password="pass")

    @config_email_disabled
    def test_authenticate_username_not_validated_by_email_no_email(self):
        """Test to authenticate when not validated by email and emails disabled."""
        self.user.validated_by_email = False
        self.user.validated_by_manager = True
        self.user.save()

        backend = DakaraModelBackend()
        self.assertEqual(
            backend.authenticate(MagicMock(), username="TestUser", password="pass"),
            self.user,
        )

    def test_authenticate_username_not_validated_by_manager(self):
        """Test to authenticate when not validated by manager."""
        self.user.validated_by_email = True
        self.user.validated_by_manager = False
        self.user.save()

        backend = DakaraModelBackend()
        with self.assertRaisesRegex(
            ValidationError, "This user account has not been validated by a manager"
        ):
            backend.authenticate(MagicMock(), username="TestUser", password="pass")

    def test_authenticate_username_ok(self):
        """Test to authenticate."""
        self.user.validated_by_email = True
        self.user.validated_by_manager = True
        self.user.save()

        backend = DakaraModelBackend()
        self.assertEqual(
            backend.authenticate(MagicMock(), username="TestUser", password="pass"),
            self.user,
        )
