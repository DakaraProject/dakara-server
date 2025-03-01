from django.urls import reverse
from freezegun import freeze_time
from rest_framework import status

from playlist.models import Karaoke, PlayerError
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
        self.assertEqual(
            response.data["karaoke"]["id"], Karaoke.objects.get_object().id
        )
        self.assertTrue(response.data["karaoke"]["ongoing"])
        self.assertTrue(response.data["karaoke"]["can_add_to_playlist"])
        self.assertTrue(response.data["karaoke"]["player_play_next_song"])
        self.assertIn("playlist_entries", response.data)

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
        self.assertEqual(response.data["player_status"]["timing"], 0)
        self.assertIn("player_errors", response.data)
        self.assertFalse(response.data["player_errors"])
        self.assertIn("karaoke", response.data)
        self.assertTrue(response.data["karaoke"]["ongoing"])
        self.assertTrue(response.data["karaoke"]["can_add_to_playlist"])
        self.assertTrue(response.data["karaoke"]["player_play_next_song"])
        self.assertIn("playlist_entries", response.data)

    @freeze_time("1970-01-01 00:01:00")
    def test_get_playing_delayed(self):
        """Get the digest when the player is playing with delay.

        There should be no errors, the player should be playing and the karaoke
        should be running.
        """
        self.authenticate(self.user)

        # start playing
        self.player_play_next_song()

        with freeze_time("1970-01-01 00:01:02"):
            # get the digest
            response = self.client.get(self.url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            # assert the response
            self.assertIn("player_status", response.data)
            self.assertEqual(
                response.data["player_status"]["playlist_entry"]["id"], self.pe1.id
            )
            self.assertEqual(response.data["player_status"]["timing"], 2)
            self.assertIn("player_errors", response.data)
            self.assertIn("karaoke", response.data)

    @freeze_time("1970-01-01 00:01:00")
    def test_get_playing_transition(self):
        """Get the digest when the player is playing a transition.

        The player should be playing but with a null timing.
        """
        self.authenticate(self.user)

        # start playing
        self.player_play_next_song(in_transition=True)

        with freeze_time("1970-01-01 00:01:01"):
            # get the digest
            response = self.client.get(self.url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            # assert the response
            self.assertEqual(response.data["player_status"]["timing"], 0)
            self.assertIn("playlist_entries", response.data)

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
            response.data["player_errors"][0]["playlist_entry"]["song"]["id"],
            errors[0].playlist_entry.song.id,
        )
        self.assertNotIn(
            "artists", response.data["player_errors"][0]["playlist_entry"]["song"]
        )
        self.assertEqual(
            response.data["player_errors"][1]["playlist_entry"]["id"],
            errors[1].playlist_entry.id,
        )
        self.assertIn("karaoke", response.data)
        self.assertTrue(response.data["karaoke"]["ongoing"])
        self.assertTrue(response.data["karaoke"]["can_add_to_playlist"])
        self.assertTrue(response.data["karaoke"]["player_play_next_song"])
        self.assertIn("playlist_entries", response.data)

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
        self.assertIn("karaoke", response.data)
        self.assertIn("playlist_entries", response.data)

    def test_get_entries(self):
        """Get the digest when there are errors.

        There should errors, the player should be idle and the karaoke
        should be running.
        """
        self.authenticate(self.user)

        # get the digest
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # assert the response
        self.assertIn("player_status", response.data)
        self.assertIn("karaoke", response.data)
        self.assertIn("player_errors", response.data)
        self.assertIn("playlist_entries", response.data)
        self.assertEqual(len(response.data["playlist_entries"]), 4)
        pe1 = response.data["playlist_entries"][0]
        self.assertEqual(pe1["id"], self.pe1.id)
        self.assertEqual(pe1["song"]["id"], self.pe1.song.id)
        self.assertNotIn("artists", pe1["song"])
        self.assertFalse(pe1["use_instrumental"])
        self.assertFalse(pe1["was_played"])
        self.assertIsNone(pe1["date_play"])
        pe2 = response.data["playlist_entries"][1]
        self.assertEqual(pe2["id"], self.pe2.id)
        self.assertEqual(pe2["song"]["id"], self.pe2.song.id)
        self.assertTrue(pe2["use_instrumental"])
        self.assertFalse(pe2["was_played"])
        self.assertIsNone(pe2["date_play"])
        pe3 = response.data["playlist_entries"][2]
        self.assertEqual(pe3["id"], self.pe3.id)
        self.assertEqual(pe3["song"]["id"], self.pe3.song.id)
        self.assertFalse(pe3["use_instrumental"])
        self.assertTrue(pe3["was_played"])
        self.assertIsNotNone(pe3["date_play"])
        pe4 = response.data["playlist_entries"][3]
        self.assertEqual(pe4["id"], self.pe4.id)
        self.assertEqual(pe4["song"]["id"], self.pe4.song.id)
        self.assertFalse(pe4["use_instrumental"])
        self.assertTrue(pe4["was_played"])
        self.assertIsNotNone(pe4["date_play"])
