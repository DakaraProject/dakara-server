import pytest

from users import models


@pytest.mark.django_db
class TestDakaraUser:
    """Test the DakaraUser closs
    """

    def test_create_user_non_case_unique(self):
        """Test to create to users with just a variation in case
        """
        models.DakaraUser.objects.create_user(username="TestUser", password="pass")

        with pytest.raises(
            models.UserExistsWithDifferentCaseError,
            match="The username must be case insensitively unique",
        ):
            models.DakaraUser.objects.create_user(username="testuser", password="pass")

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
        assert not superuser.is_playlist_user
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
