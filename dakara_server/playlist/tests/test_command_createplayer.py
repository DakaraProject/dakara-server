from io import StringIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db import transaction
from django.test import TestCase

from playlist.management.commands.createplayer import Command

UserModel = get_user_model()


class CreatePlayerCommandTestCase(TestCase):
    """Test the create player command."""

    @patch("playlist.management.commands.createplayer.input")
    def test_get_username(self, mocked_input):
        """Test to get username."""
        mocked_input.return_value = "user_value"
        username = Command.get_username()
        self.assertEqual(username, "user_value")

    @patch("playlist.management.commands.createplayer.input")
    def test_get_username_default(self, mocked_input):
        """Test to get default username."""
        mocked_input.return_value = ""
        username = Command.get_username()
        self.assertEqual(username, "player")

    @patch("playlist.management.commands.createplayer.getpass")
    def test_get_password(self, mocked_getpass):
        """Test to get password."""
        mocked_getpass.return_value = "password"
        password = Command().get_password()
        self.assertEqual(password, "password")

    @patch("playlist.management.commands.createplayer.getpass")
    def test_get_password_different(self, mocked_getpass):
        """Test to get password with difference in inputs."""
        output = StringIO()
        mocked_getpass.side_effect = ["p", "a", "p", "p"]
        password = Command(stderr=output).get_password()
        self.assertEqual(password, "p")
        self.assertListEqual(
            output.getvalue().split("\n"), ["Error: Your passwords didn't match.", ""]
        )

    def test_create_player(self):
        """Test to create a player user."""
        output = StringIO()

        # pre assert there are no users
        self.assertEqual(UserModel.objects.all().count(), 0)

        # call command
        Command(stderr=output, stdout=output).create_player("player", "pass")

        # assert there is one user of type player
        self.assertEqual(UserModel.objects.all().count(), 1)
        player = UserModel.objects.first()
        self.assertEqual(player.playlist_permission_level, UserModel.PLAYER)
        self.assertEqual(player.username, "player")

        self.assertListEqual(
            output.getvalue().split("\n"), ["Player created successfully.", ""]
        )

    def test_create_player_password_blank(self):
        """Test to create a player user with no password."""
        output = StringIO()

        # pre assert there are no users
        self.assertEqual(UserModel.objects.all().count(), 0)

        # call command
        Command(stderr=output, stdout=output).create_player("player", None)

        # assert there are no users
        self.assertEqual(UserModel.objects.all().count(), 0)

        self.assertListEqual(
            output.getvalue().split("\n"),
            ["Error: Blank passwords aren't allowed.", ""],
        )

    def test_create_player_exist(self):
        """Test to create a player user that already exists."""
        output = StringIO()

        # create one user already
        UserModel.objects.create_user("player", password="pass")
        self.assertEqual(UserModel.objects.all().count(), 1)

        # call command
        with transaction.atomic():
            Command(stderr=output, stdout=output).create_player("player", "pass")

        # assert there is one user of type player
        self.assertEqual(UserModel.objects.all().count(), 1)

        self.assertListEqual(
            output.getvalue().split("\n"),
            ["Error: UNIQUE constraint failed: users_dakarauser.username", ""],
        )

    @patch.object(Command, "get_password")
    @patch.object(Command, "get_username")
    @patch.object(Command, "create_player")
    def test_handle_non_interactive(
        self, mocked_create_player, mocked_get_username, mocked_get_password
    ):
        """Test to handle command non interactively."""
        call_command("createplayer", noinput=True, password="pass")
        mocked_create_player.assert_called_with("player", "pass")
        mocked_get_username.assert_not_called()
        mocked_get_password.assert_not_called()

    @patch.object(Command, "get_password")
    @patch.object(Command, "get_username")
    @patch.object(Command, "create_player")
    def test_handle_interactive(
        self, mocked_create_player, mocked_get_username, mocked_get_password
    ):
        """Test to handle command interactively."""
        mocked_get_username.return_value = "player"
        mocked_get_password.return_value = "pass"

        # no username, no password
        call_command("createplayer")
        mocked_create_player.assert_called_with("player", "pass")
        mocked_get_username.assert_called_with()
        mocked_get_password.assert_called_with()

        mocked_create_player.reset_mock()
        mocked_get_username.reset_mock()
        mocked_get_password.reset_mock()

        # username, no password
        call_command("createplayer", username="player")
        mocked_create_player.assert_called_with("player", "pass")
        mocked_get_username.assert_not_called()
        mocked_get_password.assert_called_with()

        mocked_create_player.reset_mock()
        mocked_get_username.reset_mock()
        mocked_get_password.reset_mock()

        # no username, password
        call_command("createplayer", password="pass")
        mocked_create_player.assert_called_with("player", "pass")
        mocked_get_username.assert_called_with()
        mocked_get_password.assert_not_called()

        mocked_create_player.reset_mock()
        mocked_get_username.reset_mock()
        mocked_get_password.reset_mock()

        # username, password
        call_command("createplayer", username="player", password="pass")
        mocked_create_player.assert_called_with("player", "pass")
        mocked_get_username.assert_not_called()
        mocked_get_password.assert_not_called()
