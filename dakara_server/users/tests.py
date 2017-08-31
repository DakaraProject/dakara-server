from django.core.urlresolvers import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from .base_test import BaseAPITestCase

UserModel = get_user_model()

class UsersListCreateAPIViewTestCase(BaseAPITestCase):
    url = reverse('users-list')

    def setUp(self):
        # create a user without any rights
        self.user = self.create_user("TestUser")

        # Create a users manager
        self.manager = self.create_user("TestUserManager", users_level="m")

    def test_get_users_list(self):
        """
        Test to verify users list
        """
        # Login as simple user 
        self.authenticate(self.user)

        # Get users list
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(len(response.data['results']), 2)

    def test_get_users_list_forbidden(self):
        """
        Test to verify users list is not available when not logged in
        """
        # Get users list
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_post_create_user(self):
        """
        Test to verify user creation
        """
        # Login as manager
        self.authenticate(self.manager)

        # Post new user
        username_new_user = "TestUserNew"
        response = self.client.post(self.url,
                {"username": username_new_user, "password": "pwd"})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check user has been created in database
        self.assertEqual(UserModel.objects.count(), 3)
        new_user = UserModel.objects.get(username=username_new_user)
        self.assertEqual(new_user.username, username_new_user)

    def test_post_create_user_forbidden(self):
        """
        Test to verify simple user cannot create users
        """
        # Login as simple user 
        self.authenticate(self.user)

        # Post new user
        username_new_user = "TestUserNew"
        response = self.client.post(self.url,
                {"username": username_new_user, "password": "pwd"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_post_create_user_already_exists(self):
        """
        Test to verify user cannot be created when the username is already taken
        This test also ensure username check is case insensitive
        """
        # Login as manager
        self.authenticate(self.manager)

        # Post new user with same name as existing user
        username_new_user = self.user.username
        response = self.client.post(self.url,
                {"username": username_new_user, "password": "pwd"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Post new user with same name as existing user
        # But with different case
        username_new_user = self.user.username.upper()
        response = self.client.post(self.url,
                {"username": username_new_user, "password": "pwd"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UsersRetrieveUpdateDestroyTestCase(BaseAPITestCase):

    def setUp(self):
        # create a user without any rights
        self.user = self.create_user("TestUser")

        # Create a users manager
        self.manager = self.create_user("TestUserManager", users_level="m")

        # Generate url to access these users
        self.user_url = reverse('users-detail', kwargs={"pk": self.user.id})
        self.manager_url = reverse('users-detail', kwargs={"pk": self.manager.id})

    def test_get_user(self):
        """
        Test to verify user details
        """
        # Login as simple user
        self.authenticate(self.user)

        # Get simple user details
        response = self.client.get(self.user_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {
                    "id": self.user.id,
                    "username": self.user.username,
                    "is_superuser": self.user.is_superuser,
                    "users_permission_level": self.user.users_permission_level,
                    "library_permission_level": self.user.library_permission_level,
                    "playlist_permission_level": self.user.playlist_permission_level
                })

        # Get manager details
        response = self.client.get(self.manager_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {
                    "id": self.manager.id,
                    "username": self.manager.username,
                    "is_superuser": self.manager.is_superuser,
                    "users_permission_level": self.manager.users_permission_level,
                    "library_permission_level": self.manager.library_permission_level,
                    "playlist_permission_level": self.manager.playlist_permission_level
                })

    def test_get_user_forbidden(self):
        """
        Test to verify user details not available when not logged in
        """
        # Get simple user details
        response = self.client.get(self.user_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_patch_user(self):
        """
        Test to verify user update
        """
        # Pre-assertion: user has no library rights
        user = UserModel.objects.get(id=self.user.id)
        self.assertEqual(user.library_permission_level, None)

        # Login as manager
        self.authenticate(self.manager)

        # update simple user to library user
        response = self.client.patch(self.user_url, {"library_permission_level": "u"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Post-assertion: user is now a library user
        user = UserModel.objects.get(id=self.user.id)
        self.assertEqual(user.library_permission_level, "u")

    def test_patch_user_forbidden_self(self):
        """
        Test to verify user update can't update self
        """
        # Login as manager
        self.authenticate(self.manager)

        # attempt to update self to library user
        response = self.client.patch(self.manager_url, {"library_permission_level": "u"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_patch_user_forbidden(self):
        """
        Test to verify simple user can't update user
        """
        # Login as simple user
        self.authenticate(self.user)

        # attempt to update manager to library user
        response = self.client.patch(self.manager_url, {"library_permission_level": "u"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_user(self):
        """
        Test to verify user delete
        """
        # Login as manager
        self.authenticate(self.manager)

        # Delete simple user
        response = self.client.delete(self.user_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Post-assertion: user is not in database anymore 
        users = UserModel.objects.filter(id=self.user.id)
        self.assertEqual(len(users), 0)

    def test_delete_user_forbidden_self(self):
        """
        Test to verify user update can't delete self
        """
        # Login as manager
        self.authenticate(self.manager)

        # Attempt to delete self
        response = self.client.delete(self.manager_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_user_forbidden(self):
        """
        Test to verify simple user can't delete user
        """
        # Login as simple user
        self.authenticate(self.user)

        # Attempt to delete manager
        response = self.client.delete(self.manager_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class CurrentUserTestCase(BaseAPITestCase):
    url = reverse('users-current')

    def setUp(self):
        # create a user without any rights
        self.user = self.create_user("TestUser")

        # Create a users manager
        self.manager = self.create_user("TestUserManager", users_level="m")

    def test_get_current_user(self):
        """
        Test to verify get current user route
        """
        # Login as simple user
        self.authenticate(self.user)

        # Get current user
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {
                    "id": self.user.id,
                    "username": self.user.username,
                    "is_superuser": self.user.is_superuser,
                    "users_permission_level": self.user.users_permission_level,
                    "library_permission_level": self.user.library_permission_level,
                    "playlist_permission_level": self.user.playlist_permission_level
                })

        # Login as manager
        self.authenticate(self.manager)

        # Get current user
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {
                    "id": self.manager.id,
                    "username": self.manager.username,
                    "is_superuser": self.manager.is_superuser,
                    "users_permission_level": self.manager.users_permission_level,
                    "library_permission_level": self.manager.library_permission_level,
                    "playlist_permission_level": self.manager.playlist_permission_level
                })

    def test_get_current_user_forbidden(self):
        """
        Test to verify we can't get current user when not logged in
        (obviously)
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class PasswordViewTestCase(BaseAPITestCase):

    def setUp(self):
        # create a user without any rights
        self.user = self.create_user("TestUser")

        # Create a users manager
        self.manager = self.create_user("TestUserManager", users_level="m")

        # Generate url to access these users
        self.user_url = reverse('users-password', kwargs={"pk": self.user.id})
        self.manager_url = reverse('users-password', kwargs={"pk": self.manager.id})

    def test_put_password(self):
        """
        Test to verify password update
        """
        new_password = "newPassword"
        # Pre-assertion: user password is not 'newPassword'
        user = UserModel.objects.get(id=self.user.id)
        self.assertFalse(user.check_password(new_password))

        # Login as simple user
        self.authenticate(self.user)

        # update own password
        response = self.client.put(self.user_url, {
            "old_password": "password",
            "password": new_password
            })
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Post-assertion: user password is now 'newPassword'
        user = UserModel.objects.get(id=self.user.id)
        self.assertTrue(user.check_password(new_password))

    def test_put_password_wrong_password(self):
        """
        Test to verify password can't be updated if old pass is invalid
        """
        new_password = "newPassword"
        # Pre-assertion: user password is not 'newPassword'
        user = UserModel.objects.get(id=self.user.id)
        self.assertFalse(user.check_password(new_password))

        # Login as simple user
        self.authenticate(self.user)

        # update own password
        response = self.client.put(self.user_url, {
            "old_password": "WrongOldpassword",
            "password": new_password
            })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Post-assertion: user password is still not 'newPassword'
        user = UserModel.objects.get(id=self.user.id)
        self.assertFalse(user.check_password(new_password))

    def test_put_password_forbidden(self):
        """
        Test to verify one can't update other password
        """
        # Login as simple user
        self.authenticate(self.user)

        # Attempt to update manager password
        response = self.client.put(self.manager_url, {
            "old_password": "password",
            "password": "new"
            })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
