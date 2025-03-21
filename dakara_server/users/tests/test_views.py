from unittest.mock import ANY, patch

from django.urls import reverse
from rest_framework import status

from internal.tests.base_test import UserModel
from users.tests.base_test import UsersAPITestCase, config_email_disabled


class RegisterViewTestCase(UsersAPITestCase):
    url = reverse("rest_registration:register")

    @patch("users.emails.send_notification_to_managers")
    def test_create_user(self, mocked_send_notification_to_managers):
        """Test to create a user."""
        self.manager = self.create_user(
            "TestManger", email="test@manager.com", users_level=UserModel.MANAGER
        )
        response = self.client.post(
            self.url,
            {
                "username": "TestUser",
                "email": "test@user.com",
                "password": "password",
                "password_confirm": "password",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        user = UserModel.objects.last()
        mocked_send_notification_to_managers.assert_called_once_with(user)

    @patch("users.emails.send_notification_to_managers")
    def test_create_user_name_not_unique(self, mocked_send_notification_to_managers):
        """Test to create a user with same username as an existing one."""
        self.user = self.create_user("TestUser", email="test@user.com")
        response = self.client.post(
            self.url,
            {
                "username": "TestUser",
                "email": "test2@user.com",
                "password": "password",
                "password_confirm": "password",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertListEqual(
            response.data["username"], ["user with this username already exists."]
        )

        mocked_send_notification_to_managers.assert_not_called()

    @patch("users.emails.send_notification_to_managers")
    def test_create_user_name_not_case_insensitively_unique(
        self, mocked_send_notification_to_managers
    ):
        """Test to create a user with a case different username from an existing one."""
        self.user = self.create_user("TestUser", email="test@user.com")
        response = self.client.post(
            self.url,
            {
                "username": "testuser",
                "email": "test2@user.com",
                "password": "password",
                "password_confirm": "password",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertListEqual(
            response.data["username"], ["user with this username already exists."]
        )

        mocked_send_notification_to_managers.assert_not_called()

    @patch("users.emails.send_notification_to_managers")
    def test_create_user_email_not_unique(self, mocked_send_notification_to_managers):
        """Test to create a user with same email as an existing one."""
        self.user = self.create_user("TestUser", email="test@user.com")
        response = self.client.post(
            self.url,
            {
                "username": "TestUser2",
                "email": "test@user.com",
                "password": "password",
                "password_confirm": "password",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertListEqual(
            response.data["email"], ["user with this email address already exists."]
        )

        mocked_send_notification_to_managers.assert_not_called()

    @patch("users.emails.send_notification_to_managers")
    def test_create_user_email_not_case_insensitively_unique(
        self, mocked_send_notification_to_managers
    ):
        """Test to create a user with a case different email from an existing one."""
        self.user = self.create_user("TestUser", email="test@user.com")
        response = self.client.post(
            self.url,
            {
                "username": "TestUser2",
                "email": "Test@user.com",
                "password": "password",
                "password_confirm": "password",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertListEqual(
            response.data["email"], ["user with this email address already exists."]
        )

        mocked_send_notification_to_managers.assert_not_called()


class SendResetPasswordLinklViewTestCase(UsersAPITestCase):
    url = reverse("rest_registration:send-reset-password-link")

    def setUp(self):
        # create a user without any rights
        self.user = self.create_user("TestUser", email="test@user.com", password="pass")

    def test_username_insensitive(self):
        """Check send reset password link with a username with different case."""
        response = self.client.post(self.url, {"login": "testuser"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_not_found(self):
        """Check send reset password link with a non existing username."""

        response = self.client.post(self.url, {"login": "doesnotexists"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LoginViewTestCase(UsersAPITestCase):
    url = reverse("rest_registration:login")

    def setUp(self):
        # create a user without any rights
        self.user = self.create_user("TestUser", email="test@user.com", password="pass")

    def test_login_with_username(self):
        """Test login with username for an activated user."""

        # Login request
        response = self.client.post(self.url, {"login": "testuser", "password": "pass"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["detail"], "Login successful")
        self.assertIn("token", response.data)
        self.assertNotEqual(response.data["token"], "")

    def test_login_with_email(self):
        """Test login with email for an activated user."""

        # Login request
        response = self.client.post(
            self.url, {"login": "test@user.com", "password": "pass"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_login_not_validated_by_email(self):
        """Test login with for a user not validated by email."""

        # Set user not validated by email
        self.user.validated_by_email = False
        self.user.save()

        # Login request
        response = self.client.post(self.url, {"login": "testuser", "password": "pass"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertListEqual(
            response.data["non_field_errors"],
            ["This user email has not been validated"],
        )
        self.assertNotIn("token", response.data)

    @config_email_disabled
    def test_login_not_validated_by_email_email_disabled(self):
        """Test login with for a user not validated by email but email disabled
        config."""

        # Set user not validated by email
        self.user.validated_by_email = False
        self.user.save()

        # Login request
        response = self.client.post(self.url, {"login": "testuser", "password": "pass"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_login_not_validated_by_manager(self):
        """Test login with for a user not validated by manager."""

        # Set user not validated by manager
        self.user.validated_by_manager = False
        self.user.save()

        # Login request
        response = self.client.post(self.url, {"login": "testuser", "password": "pass"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertListEqual(
            response.data["non_field_errors"],
            ["This user account has not been validated by a manager"],
        )
        self.assertNotIn("token", response.data)


class UserListViewTestCase(UsersAPITestCase):
    url = reverse("users-list")

    def setUp(self):
        # create a user without any rights
        self.user = self.create_user("TestUser")

        # Create a users manager
        self.manager = self.create_user(
            "TestUserManager", users_level=UserModel.MANAGER
        )

    def test_get_users_list(self):
        """Test to verify users list."""
        # Login as simple user
        self.authenticate(self.user)

        # Get users list
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)
        self.assertEqual(len(response.data["results"]), 2)

    def test_get_users_list_unauthorized(self):
        """Test to verify users list is not available when not logged in."""
        # Get users list
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch("users.views.send_register_verification_email_notification")
    def test_create_user(self, mocked_send_email):
        """Test to verify user creation."""
        # Pre assertions
        self.assertEqual(UserModel.objects.count(), 2)

        # Login as manager
        self.authenticate(self.manager)

        # Post new user
        username_new_user = "TestUserNew"
        response = self.client.post(
            self.url,
            {
                "username": username_new_user,
                "email": "email@example.com",
                "password": "pwd",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check user has been created in database
        self.assertEqual(UserModel.objects.count(), 3)
        new_user = UserModel.objects.get(username=username_new_user)
        self.assertEqual(new_user.username, username_new_user)

        # Check verification email was sent
        mocked_send_email.assert_called_with(ANY, new_user)

    @patch("users.views.send_register_verification_email_notification")
    def test_create_user_mail_send_fail(self, mocked_send_email):
        """Test to verify user not created if mail send fail."""

        # Patch send email to raise exception
        class MailSendFailException(Exception):
            pass

        mocked_send_email.side_effect = MailSendFailException("Mail send failed.")

        # Pre assertions
        self.assertEqual(UserModel.objects.count(), 2)

        # Login as manager
        self.authenticate(self.manager)

        # Post new user
        username_new_user = "TestUserNew"
        with self.assertRaises(MailSendFailException):
            self.client.post(
                self.url,
                {
                    "username": username_new_user,
                    "email": "email@example.com",
                    "password": "pwd",
                },
            )

        # Check user has not been created in database
        self.assertEqual(UserModel.objects.count(), 2)

    @config_email_disabled
    @patch("users.views.send_register_verification_email_notification")
    def test_create_user_email_disabled(self, mocked_send_email):
        """Test user creation does not send verification email with email disabled."""
        # Login as manager
        self.authenticate(self.manager)

        # Post new user
        username_new_user = "TestUserNew"
        response = self.client.post(
            self.url,
            {
                "username": username_new_user,
                "email": "email@example.com",
                "password": "pwd",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check verification email was not sent
        mocked_send_email.assert_not_called()

    @patch("users.views.send_register_verification_email_notification")
    def test_create_user_forbidden(self, mocked_send_email):
        """Test to verify simple user cannot create users."""
        # Login as simple user
        self.authenticate(self.user)

        # Post new user
        username_new_user = "TestUserNew"
        response = self.client.post(
            self.url,
            {
                "username": username_new_user,
                "email": "email@example.com",
                "password": "pwd",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Check verification email was not sent
        mocked_send_email.assert_not_called()

    @patch("users.views.send_register_verification_email_notification")
    def test_create_superuser(self, mocked_send_email):
        """Test one cannot create a superuser."""
        # Pre assertions
        self.assertEqual(UserModel.objects.count(), 2)

        # Login as manager
        self.authenticate(self.manager)

        # Post new superuser
        username_new_user = "TestNewSuperuser"
        response = self.client.post(
            self.url,
            {
                "username": username_new_user,
                "email": "email@example.com",
                "password": "pwd",
                "is_superuser": True,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check user has been created in database and is not superuser
        self.assertEqual(UserModel.objects.count(), 3)
        new_user = UserModel.objects.get(username=username_new_user)
        self.assertFalse(new_user.is_superuser)

        # Check verification email was sent
        mocked_send_email.assert_called_with(ANY, new_user)

    @patch("users.views.send_register_verification_email_notification")
    def test_create_user_name_already_exists(self, mocked_send_email):
        """Test for duplicated users.

        Verify user cannot be created when the username is already taken. This
        test also ensure username check is case insensitive.
        """
        # Login as manager
        self.authenticate(self.manager)

        # Post new user with same name as existing user
        username_new_user = self.user.username
        response = self.client.post(
            self.url,
            {
                "username": username_new_user,
                "email": "email@example.com",
                "password": "pwd",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Post new user with same name as existing user
        # But with different case
        username_new_user = self.user.username.upper()
        response = self.client.post(
            self.url, {"username": username_new_user, "password": "pwd"}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Check verification email was not sent
        mocked_send_email.assert_not_called()


class UserViewTestCase(UsersAPITestCase):
    def setUp(self):
        # create a user without any rights
        self.user = self.create_user("TestUser")

        # Create a users manager
        self.manager = self.create_user(
            "TestUserManager", users_level=UserModel.MANAGER
        )

        # Generate url to access these users
        self.user_url = reverse("users", kwargs={"pk": self.user.id})
        self.manager_url = reverse("users", kwargs={"pk": self.manager.id})

    def test_get_user(self):
        """Test to verify user details."""
        # Login as simple user
        self.authenticate(self.user)

        # Get simple user details
        response = self.client.get(self.user_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(
            response.data,
            {
                "id": self.user.id,
                "username": self.user.username,
                "is_superuser": self.user.is_superuser,
                "users_permission_level": self.user.users_permission_level,
                "library_permission_level": self.user.library_permission_level,
                "playlist_permission_level": self.user.playlist_permission_level,
            },
        )

        # Get manager details
        response = self.client.get(self.manager_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(
            response.data,
            {
                "id": self.manager.id,
                "username": self.manager.username,
                "is_superuser": self.manager.is_superuser,
                "users_permission_level": self.manager.users_permission_level,
                "library_permission_level": self.manager.library_permission_level,
                "playlist_permission_level": self.manager.playlist_permission_level,
            },
        )

    def test_get_user_as_manager(self):
        """Test to verify user details."""
        # Login as user manager
        self.authenticate(self.manager)

        # Get simple user details
        response = self.client.get(self.user_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(
            response.data,
            {
                "id": self.user.id,
                "username": self.user.username,
                "email": self.user.email,
                "is_superuser": self.user.is_superuser,
                "users_permission_level": self.user.users_permission_level,
                "library_permission_level": self.user.library_permission_level,
                "playlist_permission_level": self.user.playlist_permission_level,
                "validated_by_manager": self.user.validated_by_manager,
                "validated_by_email": self.user.validated_by_email,
            },
        )

    def test_get_user_unauthorized(self):
        """Test to verify user details not available when not logged in."""
        # Get simple user details
        response = self.client.get(self.user_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch("users.emails.send_notification_to_user_validated")
    def test_patch_user(self, mocked_send_notification_to_user_validated):
        """Test to verify user update."""
        # Pre-assertion: user has no library rights
        user = UserModel.objects.get(id=self.user.id)
        self.assertEqual(user.library_permission_level, None)

        # Login as manager
        self.authenticate(self.manager)

        # update simple user to library user
        response = self.client.patch(
            self.user_url, {"library_permission_level": UserModel.USER}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Post-assertion: user is now a library user
        user = UserModel.objects.get(id=self.user.id)
        self.assertEqual(user.library_permission_level, UserModel.USER)

        # assert no mail was sent, as the edition did not change account validation
        mocked_send_notification_to_user_validated.assert_not_called()

    def test_patch_user_cant_edit_password(self):
        """Test to verify manager can't edit password when mail enabled."""
        # Keep old user password
        old_user_password = UserModel.objects.get(id=self.user.id).password

        # Login as manager
        self.authenticate(self.manager)

        # attempt to update password
        response = self.client.patch(self.user_url, {"password": "newPass"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Post-assertion: user password is unchanged
        user = UserModel.objects.get(id=self.user.id)
        self.assertEqual(user.password, old_user_password)

    @config_email_disabled
    def test_patch_user_edit_password(self):
        """Test to verify manager can edit password when mail disabled."""
        # Keep old user password
        old_user_password = UserModel.objects.get(id=self.user.id).password

        # Login as manager
        self.authenticate(self.manager)

        # Update password
        response = self.client.patch(self.user_url, {"password": "newPass"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Post-assertion: user password is unchanged
        user = UserModel.objects.get(id=self.user.id)
        self.assertNotEqual(user.password, old_user_password)

    @patch("users.emails.send_notification_to_user_validated")
    def test_patch_user_validate_by_manager(
        self, mocked_send_notification_to_user_validated
    ):
        """Test to verify user validation by a manager."""
        # Set user as not validated
        self.user.validated_by_manager = False
        self.user.save()

        # Login as manager
        self.authenticate(self.manager)

        # validate user
        response = self.client.patch(self.user_url, {"validated_by_manager": True})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Post-assertion: user is now validated
        user = UserModel.objects.get(id=self.user.id)
        self.assertTrue(user.validated_by_manager)

        # assert mail was sent
        mocked_send_notification_to_user_validated.assert_called_once_with(user)

    def test_patch_self_forbidden(self):
        """Test to verify user update can't update self."""
        # Login as manager
        self.authenticate(self.manager)

        # attempt to update self to library user
        response = self.client.patch(
            self.manager_url, {"library_permission_level": UserModel.USER}
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_patch_user_forbidden(self):
        """Test to verify simple user can't update user."""
        # Login as simple user
        self.authenticate(self.user)

        # attempt to update manager to library user
        response = self.client.patch(
            self.manager_url, {"library_permission_level": UserModel.USER}
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_patch_superuser_not_possible(self):
        """Test one cannot set a superuser."""
        # Pre-assertion: user is not superuser
        user = UserModel.objects.get(id=self.user.id)
        self.assertFalse(user.is_superuser)

        # Login as manager
        self.authenticate(self.manager)

        # update simple user to library user
        response = self.client.patch(self.user_url, {"is_superuser": True})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Post-assertion: user is still not superuser
        user = UserModel.objects.get(id=self.user.id)
        self.assertFalse(user.is_superuser)

    def test_delete_user(self):
        """Test to verify user delete."""
        # Login as manager
        self.authenticate(self.manager)

        # Delete simple user
        response = self.client.delete(self.user_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Post-assertion: user is not in database anymore
        users = UserModel.objects.filter(id=self.user.id)
        self.assertEqual(len(users), 0)

    def test_delete_self_forbidden(self):
        """Test to verify user update can't delete self."""
        # Login as manager
        self.authenticate(self.manager)

        # Attempt to delete self
        response = self.client.delete(self.manager_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_user_forbidden(self):
        """Test to verify simple user can't delete user."""
        # Login as simple user
        self.authenticate(self.user)

        # Attempt to delete manager
        response = self.client.delete(self.manager_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class CurrentUserViewTestCase(UsersAPITestCase):
    url = reverse("users-current")

    def setUp(self):
        # create a user without any rights
        self.user = self.create_user("TestUser")

        # Create a users manager
        self.manager = self.create_user(
            "TestUserManager", users_level=UserModel.MANAGER
        )

    def test_get_current_user(self):
        """Test to verify get current user route."""
        # Login as simple user
        self.authenticate(self.user)

        # Get current user
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(
            response.data,
            {
                "id": self.user.id,
                "username": self.user.username,
                "email": self.user.email,
                "is_superuser": self.user.is_superuser,
                "validated_by_email": self.user.validated_by_email,
                "users_permission_level": self.user.users_permission_level,
                "library_permission_level": self.user.library_permission_level,
                "playlist_permission_level": self.user.playlist_permission_level,
            },
        )

        # Login as manager
        self.authenticate(self.manager)

        # Get current user
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(
            response.data,
            {
                "id": self.manager.id,
                "username": self.manager.username,
                "email": self.manager.email,
                "is_superuser": self.manager.is_superuser,
                "validated_by_email": self.manager.validated_by_email,
                "users_permission_level": self.manager.users_permission_level,
                "library_permission_level": self.manager.library_permission_level,
                "playlist_permission_level": self.manager.playlist_permission_level,
            },
        )

    def test_get_current_user_unauthorized(self):
        """Test to verify we can't get current user when not logged in.

        (Obviously.)
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
