from unittest.mock import patch
from datetime import datetime

from django.core.urlresolvers import reverse
from django.utils import timezone
from rest_framework import status

from playlist.models import PlayerError
from playlist.tests.base_test import BaseAPITestCase

tz = timezone.get_default_timezone()


class PlayerErrorViewTestCase(BaseAPITestCase):
    """Test the view of the player errors"""

    url = reverse("playlist-player-errors")

    def setUp(self):
        self.create_test_data()

    def test_get_errors_empty(self):
        """Test to get errors when there are none"""
        # pre assert
        self.assertEqual(PlayerError.objects.count(), 0)

        # log as user
        self.authenticate(self.user)

        # request the errors list
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # assert the response
        self.assertEqual(response.data["results"], [])

    def test_get_errors_something(self):
        """Test to get errors when there is an error"""
        # set an error
        PlayerError.objects.create(playlist_entry=self.pe1, error_message="dummy error")

        # log as user
        self.authenticate(self.user)

        # request the errors list
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # assert the response
        self.assertEqual(
            response.data["results"][0]["playlist_entry"]["id"], self.pe1.id
        )
        self.assertEqual(response.data["results"][0]["error_message"], "dummy error")

    def test_get_errors_forbidden(self):
        """Test to get errors when not authenticated"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch("playlist.views.broadcast_to_channel")
    def test_post_error_success(self, mocked_broadcast_to_channel):
        """Test to create an error"""
        # pre assert
        self.assertEqual(PlayerError.objects.count(), 0)

        # start playing
        self.pe1.date_played = datetime.now(tz)
        self.pe1.save()

        # log as player
        self.authenticate(self.player)

        # request to create an error
        response = self.client.post(
            self.url,
            data={"playlist_entry_id": self.pe1.id, "error_message": "dummy error"},
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # assert the result
        self.assertEqual(PlayerError.objects.count(), 1)
        player_error = PlayerError.objects.first()
        self.assertEqual(player_error.playlist_entry, self.pe1)
        self.assertEqual(player_error.error_message, "dummy error")

        # assert the event has been broadcasted
        mocked_broadcast_to_channel.assert_called_with(
            "playlist.front", "send_player_error", {"player_error": player_error}
        )

    def test_post_error_failed_wrong_playlist_entry(self):
        """Test to create an error with another playlist entry"""
        # pre assert
        self.assertEqual(PlayerError.objects.count(), 0)

        # start playing
        self.pe1.date_played = datetime.now(tz)
        self.pe1.save()

        # log as player
        self.authenticate(self.player)

        # request to create an error
        response = self.client.post(
            self.url,
            data={"playlist_entry_id": self.pe2.id, "error_message": "dummy error"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # assert the result
        self.assertEqual(PlayerError.objects.count(), 0)

    def test_post_error_failed_no_current_playlist_entry(self):
        """Test to create an error when no playlist entry is playing"""
        # pre assert
        self.assertEqual(PlayerError.objects.count(), 0)

        # log as player
        self.authenticate(self.player)

        # request to create an error
        response = self.client.post(
            self.url,
            data={"playlist_entry_id": self.pe2.id, "error_message": "dummy error"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # assert the result
        self.assertEqual(PlayerError.objects.count(), 0)

    def test_post_error_forbidden_not_authenticated(self):
        """Test to create an error when not loged in"""
        # start playing
        self.pe1.date_played = datetime.now(tz)
        self.pe1.save()

        # request to create an error
        response = self.client.post(
            self.url,
            data={"playlist_entry_id": self.pe1.id, "error_message": "dummy error"},
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_post_error_forbidden_not_player(self):
        """Test to create an error when not loged in as player"""
        # start playing
        self.pe1.date_played = datetime.now(tz)
        self.pe1.save()

        # log in as user
        self.authenticate(self.user)

        # request to create an error
        response = self.client.post(
            self.url,
            data={"playlist_entry_id": self.pe1.id, "error_message": "dummy error"},
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
