from datetime import datetime, timedelta
from unittest.mock import ANY, patch

from django.urls import reverse
from django.utils.dateparse import parse_datetime
from rest_framework import status

from internal.tests.base_test import tz
from playlist.models import Karaoke, Player, PlaylistEntry
from playlist.tests.base_test import PlaylistAPITestCase


class PlayerStatusViewTestCase(PlaylistAPITestCase):
    """Test the view of the player."""

    url = reverse("playlist-player-status")

    def setUp(self):
        self.create_test_data()

    def test_get_status_idle(self):
        """Test to access the player status when idle."""
        self.authenticate(self.user)

        # check the player is idle
        karaoke = Karaoke.objects.get_object()
        player, _ = Player.cache.get_or_create(karaoke=karaoke)
        self.assertIsNone(player.playlist_entry)

        # assert the status of the player
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data["playlist_entry"])
        self.assertEqual(response.data["timing"], 0)
        self.assertFalse(response.data["paused"])
        self.assertEqual(parse_datetime(response.data["date"]), player.date)

    def test_get_status_in_transition(self):
        """Test to access the player status when in transition."""
        self.authenticate(self.user)

        # set the player in transition
        player = self.player_play_next_song(in_transition=True)

        # assert the status of the player
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["playlist_entry"]["id"], self.pe1.id)
        self.assertTrue(response.data["in_transition"])
        self.assertEqual(response.data["timing"], 0)
        self.assertFalse(response.data["paused"])
        self.assertEqual(parse_datetime(response.data["date"]), player.date)

    def test_get_status_in_play_with_timing(self):
        """Test to access the player status when in play with timing."""
        self.authenticate(self.user)

        # set the player in play
        player = self.player_play_next_song(timing=timedelta(seconds=2))

        # assert the status of the player
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["playlist_entry"]["id"], self.pe1.id)
        self.assertFalse(response.data["in_transition"])
        self.assertEqual(response.data["timing"], 2)
        self.assertFalse(response.data["paused"])
        self.assertEqual(parse_datetime(response.data["date"]), player.date)

    def test_get_status_in_pause_with_timing(self):
        """Test to access the player status when in pause with timing."""
        self.authenticate(self.user)

        # set the player in play
        player = self.player_play_next_song(timing=timedelta(seconds=5), paused=True)

        # assert the status of the player
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["playlist_entry"]["id"], self.pe1.id)
        self.assertFalse(response.data["in_transition"])
        self.assertEqual(response.data["timing"], 5)
        self.assertTrue(response.data["paused"])
        self.assertEqual(parse_datetime(response.data["date"]), player.date)

    def test_get_status_forbidden(self):
        """Test to access the player status when not loged in."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch("playlist.views.send_to_channel")
    @patch(
        "django.db.models.fields.timezone.now",
    )
    def test_put_status_started_transition(self, mocked_now, mocked_send_to_channel):
        """Test player started transition."""
        # patch the now method
        now = datetime.now(tz)
        mocked_now.return_value = now

        self.authenticate(self.player)

        # perform the request
        response = self.client.put(
            self.url,
            data={
                "event": "started_transition",
                "playlist_entry_id": self.pe1.id,
                "timing": 0,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # assert the response
        self.assertEqual(response.data["playlist_entry"]["id"], self.pe1.id)
        self.assertFalse(response.data["paused"])
        self.assertTrue(response.data["in_transition"])
        self.assertEqual(response.data["timing"], 0)

        # assert the result
        karaoke = Karaoke.objects.get_object()
        player, _ = Player.cache.get_or_create(karaoke=karaoke)
        self.assertEqual(player.playlist_entry, self.pe1)
        self.assertFalse(player.paused)
        self.assertEqual(player.timing, timedelta(0))
        self.assertTrue(player.in_transition)
        self.assertEqual(player.date, now)

        # # assert an event has been broadcasted to the front
        # mocked_send_to_channel.assert_called_with(
        #     "playlist.front", "send_player_status", {"player": player}
        # )

    def test_put_status_started_transition_with_timing(self):
        """Test timing is 0 during transition."""
        self.authenticate(self.player)

        # perform the request
        response = self.client.put(
            self.url,
            data={
                "event": "started_transition",
                "playlist_entry_id": self.pe1.id,
                "timing": 2,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # assert the response
        self.assertEqual(response.data["playlist_entry"]["id"], self.pe1.id)
        self.assertFalse(response.data["paused"])
        self.assertTrue(response.data["in_transition"])
        self.assertEqual(response.data["timing"], 0)

        # assert the result
        karaoke = Karaoke.objects.get_object()
        player, _ = Player.cache.get_or_create(karaoke=karaoke)
        self.assertEqual(player.timing, timedelta(0))

        # assert extra fields have not been saved
        self.assertFalse(hasattr(player, "event"))

    @patch("playlist.views.send_to_channel")
    @patch(
        "django.db.models.fields.timezone.now",
    )
    def test_put_status_started_song(self, mocked_now, mocked_send_to_channel):
        """Test player finished transition."""
        # patch the now method
        now = datetime.now(tz)
        mocked_now.return_value = now

        self.authenticate(self.player)

        # set the player already in transition
        self.player_play_next_song(in_transition=True)

        # perform the request
        response = self.client.put(
            self.url,
            data={
                "event": "started_song",
                "playlist_entry_id": self.pe1.id,
                "timing": 0,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # assert the response
        self.assertEqual(response.data["playlist_entry"]["id"], self.pe1.id)
        self.assertFalse(response.data["paused"])
        self.assertFalse(response.data["in_transition"])
        self.assertEqual(response.data["timing"], 0)

        # assert the result
        karaoke = Karaoke.objects.get_object()
        player, _ = Player.cache.get_or_create(karaoke=karaoke)
        self.assertEqual(player.playlist_entry, self.pe1)
        self.assertFalse(player.paused)
        self.assertEqual(player.timing, timedelta(0))
        self.assertFalse(player.in_transition)
        self.assertEqual(player.date, now)

        # # assert an event has been broadcasted to the front
        # mocked_send_to_channel.assert_called_with(
        #     "playlist.front", "send_player_status", {"player": player}
        # )

    @patch("playlist.views.send_to_channel")
    @patch(
        "django.db.models.fields.timezone.now",
    )
    def test_put_status_resumed(self, mocked_now, mocked_send_to_channel):
        """Test event played resumed."""
        # patch the now method
        now = datetime.now(tz)
        mocked_now.return_value = now

        self.authenticate(self.player)

        # set the player already in play
        self.player_play_next_song(timing=timedelta(seconds=1), paused=True)

        # perform the request
        response = self.client.put(
            self.url,
            data={"event": "resumed", "playlist_entry_id": self.pe1.id, "timing": 2},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # assert the response
        self.assertEqual(response.data["playlist_entry"]["id"], self.pe1.id)
        self.assertFalse(response.data["paused"])
        self.assertFalse(response.data["in_transition"])
        self.assertEqual(response.data["timing"], 2)

        # assert the result
        karaoke = Karaoke.objects.get_object()
        player, _ = Player.cache.get_or_create(karaoke=karaoke)
        self.assertEqual(player.playlist_entry, self.pe1)
        self.assertFalse(player.paused)
        self.assertEqual(player.timing, timedelta(seconds=2))
        self.assertFalse(player.in_transition)
        self.assertEqual(player.date, now)

        # # assert an event has been broadcasted to the front
        # mocked_send_to_channel.assert_called_with(
        #     "playlist.front", "send_player_status", {"player": player}
        # )

    @patch("playlist.views.send_to_channel")
    @patch(
        "django.db.models.fields.timezone.now",
    )
    def test_put_status_paused(self, mocked_now, mocked_send_to_channel):
        """Test event paused player."""
        # patch the now method
        now = datetime.now(tz)
        mocked_now.return_value = now

        self.authenticate(self.player)

        # set the player in play
        self.player_play_next_song(timing=timedelta(seconds=1))

        # perform the request
        response = self.client.put(
            self.url,
            data={"event": "paused", "playlist_entry_id": self.pe1.id, "timing": 2},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # assert the response
        self.assertEqual(response.data["playlist_entry"]["id"], self.pe1.id)
        self.assertTrue(response.data["paused"])
        self.assertFalse(response.data["in_transition"])
        self.assertEqual(response.data["timing"], 2)

        # assert the result
        karaoke = Karaoke.objects.get_object()
        player, _ = Player.cache.get_or_create(karaoke=karaoke)
        self.assertEqual(player.playlist_entry, self.pe1)
        self.assertTrue(player.paused)
        self.assertEqual(player.timing, timedelta(seconds=2))
        self.assertFalse(player.in_transition)
        self.assertEqual(player.date, now)

        # # assert an event has been broadcasted to the front
        # mocked_send_to_channel.assert_called_with(
        #     "playlist.front", "send_player_status", {"player": player}
        # )

    @patch("playlist.views.send_to_channel")
    def test_put_status_finished(self, mocked_send_to_channel):
        """Test event finished."""
        self.authenticate(self.player)

        # set the player in play
        self.player_play_next_song()

        # pre assert
        pe1 = PlaylistEntry.objects.get(pk=self.pe1.id)
        self.assertFalse(pe1.was_played)

        # perform the request
        response = self.client.put(
            self.url, data={"event": "finished", "playlist_entry_id": self.pe1.id}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # assert the player has not changed
        karaoke = Karaoke.objects.get_object()
        player, _ = Player.cache.get_or_create(karaoke=karaoke)
        self.assertIsNone(player.playlist_entry)

        # assert the response
        self.assertIsNone(response.data["playlist_entry"])
        self.assertFalse(response.data["paused"])
        self.assertFalse(response.data["in_transition"])
        self.assertEqual(response.data["timing"], 0)

        # assert the result
        pe1 = PlaylistEntry.objects.get(pk=self.pe1.id)
        self.assertTrue(pe1.was_played)

        # assert an event has been sent to the device
        mocked_send_to_channel.assert_called_with(ANY, "handle_next")

    @patch("playlist.views.send_to_channel")
    @patch(
        "django.db.models.fields.timezone.now",
    )
    def test_put_status_could_not_play(self, mocked_now, mocked_send_to_channel):
        """Test event could not play."""
        # patch the now method
        now = datetime.now(tz)
        mocked_now.return_value = now

        self.authenticate(self.player)

        # perform the request
        response = self.client.put(
            self.url, data={"event": "could_not_play", "playlist_entry_id": self.pe1.id}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # assert the response
        self.assertIsNone(response.data["playlist_entry"])
        self.assertFalse(response.data["paused"])
        self.assertFalse(response.data["in_transition"])
        self.assertEqual(response.data["timing"], 0)

        # assert the result
        karaoke = Karaoke.objects.get_object()
        player, _ = Player.cache.get_or_create(karaoke=karaoke)
        self.assertIsNone(player.playlist_entry)
        self.assertFalse(player.paused)
        self.assertEqual(player.timing, timedelta(0))
        self.assertFalse(player.in_transition)
        self.assertEqual(player.date, now)

        # assert pe1 marked as played
        pe1 = PlaylistEntry.objects.get(pk=self.pe1.id)
        self.assertTrue(pe1.was_played)

        # # assert an event has been broadcasted to the front
        # mocked_send_to_channel.assert_called_with(
        #     "playlist.front", "send_player_status", {"player": player}
        # )

    def test_put_status_failed_wrong_playlist_entry(self):
        """Test to set the player status with another playlist entry."""
        self.authenticate(self.player)

        # set the player already in play
        player_old = self.player_play_next_song(timing=timedelta(seconds=1))

        # perform the request
        response = self.client.put(
            self.url,
            data={"event": "finished", "playlist_entry_id": self.pe2.id, "timing": 2},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # assert the result
        karaoke = Karaoke.objects.get_object()
        player_new, _ = Player.cache.get_or_create(karaoke=karaoke)
        self.assertEqual(player_old, player_new)

    def test_put_status_forbidden_not_authenticated(self):
        """Test to set the player when not authenticated."""
        response = self.client.put(
            self.url,
            data={
                "event": "started_song",
                "playlist_entry_id": self.pe1.id,
                "timing": 2,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_put_status_forbidden_not_player(self):
        """Test to set the player when not a player user."""
        self.authenticate(self.user)
        response = self.client.put(
            self.url,
            data={
                "event": "started_song",
                "playlist_entry_id": self.pe1.id,
                "timing": 2,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_patch_status_invalid_missing_event(self):
        """Test missing event is rejected."""
        self.authenticate(self.player)

        # send a status without event
        response = self.client.patch(
            self.url, data={"playlist_entry_id": self.pe1.id, "timing": 2}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_put_status_invalid_wrong_event(self):
        """Test invalid event is rejected."""
        self.authenticate(self.player)

        # send a status without event
        response = self.client.put(
            self.url,
            data={"event": "invalid", "playlist_entry_id": self.pe1.id, "timing": 2},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_put_status_invalid_incoherent_event_idle(self):
        """Test incoherent event is rejected when player is idle."""
        self.authenticate(self.player)

        # the player is idle

        # send a status for finished song
        response = self.client.put(
            self.url, data={"event": "finished", "playlist_entry_id": self.pe1.id}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_put_status_invalid_incoherent_event_play(self):
        """Test incoherent event is rejected when player is playing."""
        self.authenticate(self.player)

        # the player is playing
        self.player_play_next_song()

        # send a status for finished song
        response = self.client.put(
            self.url,
            data={"event": "started_transition", "playlist_entry_id": self.pe1.id},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
