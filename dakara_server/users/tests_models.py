from unittest import TestCase

from users.models import DakaraUser


class DakaraUserTestCase(TestCase):
    """Test the Dakara user object permissions
    """

    def test_users_permission_levels(self):
        """Test the users app permission levels
        """
        # create a users user
        user = DakaraUser(username="user", users_permission_level=DakaraUser.USER)

        # assert their permissions
        self.assertTrue(user.is_users_user)
        self.assertFalse(user.is_users_manager)

        # create a users manager
        manager = DakaraUser(
            username="manager", users_permission_level=DakaraUser.MANAGER
        )

        # assert their permissions
        self.assertFalse(manager.is_users_user)
        self.assertTrue(manager.is_users_manager)

        # create a superuser
        superuser = DakaraUser(username="root", is_superuser=True)

        # assert their permissions
        self.assertFalse(superuser.is_users_user)
        self.assertFalse(superuser.is_users_manager)

    def test_library_permission_levels(self):
        """Test the library app permission levels
        """
        # create a library user
        user = DakaraUser(username="user", library_permission_level=DakaraUser.USER)

        # assert their permissions
        self.assertTrue(user.is_library_user)
        self.assertFalse(user.is_library_manager)

        # create a library manager
        manager = DakaraUser(
            username="manager", library_permission_level=DakaraUser.MANAGER
        )

        # assert their permissions
        self.assertFalse(manager.is_library_user)
        self.assertTrue(manager.is_library_manager)

        # create a superuser
        superuser = DakaraUser(username="root", is_superuser=True)

        # assert their permissions
        self.assertFalse(superuser.is_library_user)
        self.assertFalse(superuser.is_library_manager)

    def test_playlist_permission_levels(self):
        """Test the playlist app permission levels
        """
        # create a playlist user
        user = DakaraUser(username="user", playlist_permission_level=DakaraUser.USER)

        # assert their permissions
        self.assertTrue(user.is_playlist_user)
        self.assertFalse(user.is_playlist_manager)
        self.assertFalse(user.is_player)

        # create a playlist manager
        manager = DakaraUser(
            username="manager", playlist_permission_level=DakaraUser.MANAGER
        )

        # assert their permissions
        self.assertFalse(manager.is_playlist_user)
        self.assertTrue(manager.is_playlist_manager)
        self.assertFalse(manager.is_player)

        # create a player
        player = DakaraUser(
            username="player", playlist_permission_level=DakaraUser.PLAYER
        )

        # assert their permissions
        self.assertFalse(player.is_playlist_user)
        self.assertFalse(player.is_playlist_manager)
        self.assertTrue(player.is_player)

        # create a superuser
        superuser = DakaraUser(username="root", is_superuser=True)

        # assert their permissions
        self.assertFalse(superuser.is_playlist_user)
        self.assertFalse(superuser.is_playlist_manager)
        self.assertFalse(superuser.is_player)
