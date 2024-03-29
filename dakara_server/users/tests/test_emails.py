from unittest.mock import ANY, patch

from internal.tests.base_test import UserModel
from users import emails
from users.tests.base_test import UsersAPITestCase, config_email_disabled


@patch("users.emails.send_mail")
class SendNotificationToManagersTestCase(UsersAPITestCase):
    """Test the send_notification_to_managers function."""

    def test_send(self, mocked_send_mail):
        """Test send notification email to managers."""
        self.create_user(
            "TestManger", email="test@manager.com", users_level=UserModel.MANAGER
        )
        user = self.create_user("TestUser", email="test@user.com")

        emails.send_notification_to_managers(user)

        # assert call
        mocked_send_mail.assert_called_once_with(
            "New user registered", ANY, ANY, ["test@manager.com"], fail_silently=False
        )

        # assert the content of the mail
        content = mocked_send_mail.call_args_list[0][0][1]
        self.assertIn("TestUser (test@user.com)", content)
        self.assertIn("/settings/users/{}".format(user.id), content)

    @config_email_disabled
    def test_send_email_disabled(self, mocked_send_mail):
        """Test notification email to managers not sent when emails are disabled."""
        self.create_user(
            "TestManger", email="test@manager.com", users_level=UserModel.MANAGER
        )
        user = self.create_user("TestUser", email="test@user.com")

        emails.send_notification_to_managers(user)

        # assert call
        mocked_send_mail.assert_not_called()

    def test_send_no_managers(self, mocked_send_mail):
        """Test send notification email when there are no managers."""
        user = self.create_user("TestUser", email="test@user.com")

        with self.assertLogs("users.emails", "DEBUG") as logger:
            emails.send_notification_to_managers(user)

        mocked_send_mail.assert_not_called()

        self.assertListEqual(
            logger.output,
            [
                "WARNING:users.emails:No managers to send message to when validating "
                "new account of TestUser"
            ],
        )


class GetNotificationToManagersTestCase(UsersAPITestCase):
    """Test the get_notification_to_managers function."""

    def test_get(self):
        """Test to get notification template for managers."""
        user = self.create_user("TestUser", email="test@user.com")
        content = emails.get_notification_to_managers(user)

        self.assertIn("TestUser (test@user.com)", content)
        self.assertIn("http://frontend-host/settings/users/1", content)


@patch("users.emails.send_mail")
class SendNotificationToUserValidatedTestCase(UsersAPITestCase):
    """Test the send_notification_to_user_validated function."""

    def test_send(self, mocked_send_mail):
        """Test send notification to user."""
        user = self.create_user("TestUser", email="test@user.com")

        emails.send_notification_to_user_validated(user)

        mocked_send_mail.assert_called_with(
            "Account validated",
            ANY,
            ANY,
            [user.email],
            fail_silently=False,
        )

    @config_email_disabled
    def test_send_email_disabled(self, mocked_send_mail):
        """Test notification to user not sent when email disabled."""
        user = self.create_user("TestUser", email="test@user.com")

        emails.send_notification_to_user_validated(user)

        mocked_send_mail.assert_not_called()


class GetManagersEmailsTestCase(UsersAPITestCase):
    """Test get_managers_emails function."""

    def test_get_managers_emails(self):
        # Create users in database
        self.create_user("User", email="user@example.com")
        manager_validated = self.create_user(
            "ManagerValidated", email="mv@example.com", users_level=UserModel.MANAGER
        )
        manager_unvalidated = self.create_user(
            "ManagerUnValidated", email="muv@example.com", users_level=UserModel.MANAGER
        )
        manager_unvalidated.validated_by_email = False
        manager_unvalidated.save()

        # Check only validated manager is returned
        self.assertCountEqual([manager_validated.email], emails.get_managers_emails())


class GetNotificationToUserValidatedTestCase(UsersAPITestCase):
    """Test the get_notification_to_user_validated function."""

    def test_get(self):
        """Test to get notification template for validated users."""
        content = emails.get_notification_to_user_validated()

        self.assertIn("http://frontend-host/login", content)
