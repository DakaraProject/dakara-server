from unittest.mock import ANY

import pytest

from users import models


@pytest.mark.django_db
class TestDakaraUser:
    """Test the DakaraUser class
    """

    def test_users_permission_levels(self):
        """Test the users app permission levels
        """
        # create a users user
        user = models.DakaraUser(
            username="user", users_permission_level=models.DakaraUser.USER
        )

        # assert their permissions
        assert user.is_users_user
        assert not user.is_users_manager

        # create a users manager
        manager = models.DakaraUser(
            username="manager", users_permission_level=models.DakaraUser.MANAGER
        )

        # assert their permissions
        assert not manager.is_users_user
        assert manager.is_users_manager

        # create a superuser
        superuser = models.DakaraUser(username="root", is_superuser=True)

        # assert their permissions
        assert not superuser.is_users_user
        assert not superuser.is_users_manager

    def test_library_permission_levels(self):
        """Test the library app permission levels
        """
        # create a library user
        user = models.DakaraUser(
            username="user", library_permission_level=models.DakaraUser.USER
        )

        # assert their permissions
        assert user.is_library_user
        assert not user.is_library_manager

        # create a library manager
        manager = models.DakaraUser(
            username="manager", library_permission_level=models.DakaraUser.MANAGER
        )

        # assert their permissions
        assert not manager.is_library_user
        assert manager.is_library_manager

        # create a superuser
        superuser = models.DakaraUser(username="root", is_superuser=True)

        # assert their permissions
        assert not superuser.is_library_user
        assert not superuser.is_library_manager

    def test_playlist_permission_levels(self):
        """Test the playlist app permission levels
        """
        # create a default user
        user = models.DakaraUser(username="user")

        # assert their permissions
        assert user.is_playlist_user
        assert not user.is_playlist_manager
        assert not user.is_player

        # create a playlist user
        user = models.DakaraUser(
            username="user", playlist_permission_level=models.DakaraUser.USER
        )

        # assert their permissions
        assert user.is_playlist_user
        assert not user.is_playlist_manager
        assert not user.is_player

        # create a playlist manager
        manager = models.DakaraUser(
            username="manager", playlist_permission_level=models.DakaraUser.MANAGER
        )

        # assert their permissions
        assert not manager.is_playlist_user
        assert manager.is_playlist_manager
        assert not manager.is_player

        # create a player
        player = models.DakaraUser(
            username="player", playlist_permission_level=models.DakaraUser.PLAYER
        )

        # assert their permissions
        assert not player.is_playlist_user
        assert not player.is_playlist_manager
        assert player.is_player

        # create a superuser
        superuser = models.DakaraUser(username="root", is_superuser=True)

        # assert their permissions
        assert superuser.is_playlist_user
        assert not superuser.is_playlist_manager
        assert not superuser.is_player


class TestStringification:
    """Test the string methods
    """

    def test_dakara_user_str(self):
        """Test the string representation of a user
        """
        user = models.DakaraUser(username="yamadatarou", password="pass")

        assert str(user) == "yamadatarou"


@pytest.mark.django_db
class TestSendValidationEmail:
    """Test a validation email is sent when user is created
    """

    def test_send_validation_email_superuser(self, mocker):
        """Test to send message on superuser creation
        """
        mocked_send_email = mocker.patch(
            "users.signals.send_register_verification_email_notification"
        )
        superuser = models.DakaraUser.objects.create_user(
            username="root", email="root@example", password="pass", is_superuser=True
        )

        mocked_send_email.assert_called_with(ANY, superuser)

    def test_send_validation_email_superuser_email_disabled(
        self, mocker, config_email_disabled
    ):
        """Test email not sent if email disabled
        """
        mocked_send_email = mocker.patch(
            "users.signals.send_register_verification_email_notification"
        )
        models.DakaraUser.objects.create_user(
            username="root", email="root@example", password="pass", is_superuser=True
        )

        mocked_send_email.assert_not_called()

    def test_send_validation_email_normal_user(self, mocker):
        """Test to not send message on normal user creation
        """
        mocked_send_email = mocker.patch(
            "users.signals.send_register_verification_email_notification"
        )
        models.DakaraUser.objects.create_user(
            username="user", email="user@example", password="pass"
        )

        mocked_send_email.assert_not_called()
