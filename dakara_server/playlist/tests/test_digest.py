from django.urls import reverse
from rest_framework import status

from playlist.models import PlayerError
from playlist.tests.base_test import PlaylistAPITestCase


class DigestViewTestCase(PlaylistAPITestCase):
    """Test the playlist shorthand view."""

    url = reverse("playlist-digest")

    def setUp(self):
        self.create_test_data()

    def test_get_startup(self):
        """Get the digest at startup.

        There should be no errors, the player should be idle and the karaoke
        should be running.
        """
        self.authenticate(self.user)

        # get the digest
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # assert the response
        self.assertIn("player_status", response.data)
        self.assertIsNone(response.data["player_status"]["playlist_entry"])
        self.assertIn("player_errors", response.data)
        self.assertFalse(response.data["player_errors"])
        self.assertIn("karaoke", response.data)
        self.assertTrue(response.data["karaoke"]["ongoing"])
        self.assertTrue(response.data["karaoke"]["can_add_to_playlist"])
        self.assertTrue(response.data["karaoke"]["player_play_next_song"])

    def test_get_playing(self):
        """Get the digest when the player is playing.

        There should be no errors, the player should be playing and the karaoke
        should be running.
        """
        self.authenticate(self.user)

        # start playing
        self.player_play_next_song()

        # get the digest
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # assert the response
        self.assertIn("player_status", response.data)
        self.assertEqual(
            response.data["player_status"]["playlist_entry"]["id"], self.pe1.id
        )
        self.assertIn("player_errors", response.data)
        self.assertFalse(response.data["player_errors"])
        self.assertIn("karaoke", response.data)
        self.assertTrue(response.data["karaoke"]["ongoing"])
        self.assertTrue(response.data["karaoke"]["can_add_to_playlist"])
        self.assertTrue(response.data["karaoke"]["player_play_next_song"])

    def test_get_errors(self):
        """Get the digest when there are errors.

        There should errors, the player should be idle and the karaoke
        should be running.
        """
        self.authenticate(self.user)

        # create errors
        errors = [
            PlayerError.objects.create(
                playlist_entry=self.pe3, error_message="dummy error 1"
            ),
            PlayerError.objects.create(
                playlist_entry=self.pe4, error_message="dummy error 2"
            ),
        ]

        # get the digest
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # assert the response
        self.assertIn("player_status", response.data)
        self.assertIsNone(response.data["player_status"]["playlist_entry"])
        self.assertIn("player_errors", response.data)
        self.assertEqual(len(response.data["player_errors"]), 2)
        self.assertEqual(
            response.data["player_errors"][0]["playlist_entry"]["id"],
            errors[0].playlist_entry.id,
        )
        self.assertEqual(
            response.data["player_errors"][1]["playlist_entry"]["id"],
            errors[1].playlist_entry.id,
        )
        self.assertIn("karaoke", response.data)
        self.assertTrue(response.data["karaoke"]["ongoing"])
        self.assertTrue(response.data["karaoke"]["can_add_to_playlist"])
        self.assertTrue(response.data["karaoke"]["player_play_next_song"])

    def test_get_player_does_not_play_next_song(self):
        """Get the digest when the player does not play next song.

        There should be no errors, the player should be idle.
        """
        self.authenticate(self.user)

        # set player does not play next song
        self.set_karaoke(player_play_next_song=False)

        # get the digest
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # assert the response
        self.assertIn("player_status", response.data)
        self.assertIsNone(response.data["player_status"]["playlist_entry"])
        self.assertIn("player_errors", response.data)
        self.assertFalse(response.data["player_errors"])
        self.assertIn("karaoke", response.data)
        self.assertFalse(response.data["karaoke"]["player_play_next_song"])
