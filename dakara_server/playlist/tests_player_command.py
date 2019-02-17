from unittest.mock import patch

from django.core.urlresolvers import reverse
from rest_framework import status

from .base_test import BaseAPITestCase


class PlayerCommandViewTestCase(BaseAPITestCase):
    """Test the commands given to the player
    """

    url = reverse("playlist-player-command")

    def setUp(self):
        self.create_test_data()

    @patch("playlist.views.broadcast_to_channel")
    def test_put_command(self, mocked_broadcast_to_channel):
        """Test to send a command (pause)
        """
        # start to play something
        self.player_play_next_song()

        # authenticate
        self.authenticate(self.manager)

        # send the command
        response = self.client.put(self.url, {"command": "pause"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # assert the response
        self.assertEqual(response.data["command"], "pause")

        # assert the side effect
        mocked_broadcast_to_channel.assert_called_once_with(
            "playlist.device", "send_command", {"command": "pause"}
        )

    @patch("playlist.views.broadcast_to_channel")
    def test_put_command_user(self, mocked_broadcast_to_channel):
        """Test to test pausing player as user
        """
        # play next song
        self.player_play_next_song()

        # login as playlist user
        self.authenticate(self.p_user)

        # request pause
        # not able to pause other's entry
        response = self.client.put(self.url, {"command": "pause"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # assert there is no side effects
        mocked_broadcast_to_channel.assert_not_called()

        # play next song and reset mock
        self.player_play_next_song()
        mocked_broadcast_to_channel.reset_mock()

        # request pause
        # able to pause own entry
        response = self.client.put(self.url, {"command": "pause"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # assert the side effect
        mocked_broadcast_to_channel.assert_called_once_with(
            "playlist.device", "send_command", {"command": "pause"}
        )

    @patch("playlist.views.broadcast_to_channel")
    def test_put_command_karaoke_not_ongoing_forbidden(
        self, mocked_broadcast_to_channel
    ):
        """Test a user cannot pause a song if the kara is not ongoing
        """
        # play next song
        self.player_play_next_song()

        # authenticate manager
        self.authenticate(self.manager)

        # set karaoke not ongoing
        self.set_karaoke(ongoing=False)

        # request pause
        response = self.client.put(self.url, {"command": "pause"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # assert there is no side effects
        mocked_broadcast_to_channel.assert_not_called()

    @patch("playlist.views.broadcast_to_channel")
    def test_put_command_player_idle_forbidden(self, mocked_broadcast_to_channel):
        """Test a user cannot pause a song if the player is idle
        """
        # authenticate manager
        self.authenticate(self.manager)

        # request pause
        response = self.client.put(self.url, {"command": "pause"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # assert there is no side effects
        mocked_broadcast_to_channel.assert_not_called()

    @patch("playlist.views.broadcast_to_channel")
    def test_put_command_incorrect_forbidden(self, mocked_broadcast_to_channel):
        """Test to send an incorrect command
        """
        # start to play something
        self.player_play_next_song()

        # authenticate
        self.authenticate(self.manager)

        # send the command
        response = self.client.put(self.url, {"command": "incorrect"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # assert the side effect
        mocked_broadcast_to_channel.assert_not_called()

    @patch("playlist.views.broadcast_to_channel")
    def test_put_command_unauthenticated_forbidden(self, mocked_broadcast_to_channel):
        """Test to send a command when not authenticated
        """
        # start to play something
        self.player_play_next_song()

        # send the command
        response = self.client.put(self.url, {"command": "incorrect"})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
