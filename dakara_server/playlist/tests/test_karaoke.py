from unittest.mock import ANY, patch

from datetime import datetime

from django.urls import reverse
from django.utils.dateparse import parse_datetime
from rest_framework import status

from internal.tests.base_test import tz
from playlist.models import Karaoke, PlaylistEntry, PlayerError
from playlist.date_stop import clear_date_stop, KARAOKE_JOB_NAME
from playlist.tests.base_test import PlaylistAPITestCase


class KaraokeViewTestCase(PlaylistAPITestCase):
    url = reverse("playlist-karaoke")
    url_digest = reverse("playlist-digest")

    def setUp(self):
        self.create_test_data()

    def test_get_karaoke(self):
        """Test an authenticated user can access the karaoke
        """
        # set stop date
        karaoke = Karaoke.objects.get_object()
        date_stop = datetime.now(tz)
        karaoke.date_stop = date_stop
        karaoke.save()

        # login as simple user
        self.authenticate(self.user)

        # get karaoke
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["ongoing"])
        self.assertTrue(response.data["can_add_to_playlist"])
        self.assertTrue(response.data["player_play_next_song"])
        self.assertEqual(parse_datetime(response.data["date_stop"]), date_stop)

        # Get karaoke again but through digest route
        response = self.client.get(self.url_digest)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["karaoke"]["ongoing"])
        self.assertTrue(response.data["karaoke"]["can_add_to_playlist"])
        self.assertTrue(response.data["karaoke"]["player_play_next_song"])
        self.assertEqual(
            parse_datetime(response.data["karaoke"]["date_stop"]), date_stop
        )

    def test_get_karaoke_forbidden(self):
        """Test an unauthenticated user cannot access the karaoke
        """
        # get karaoke
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch("playlist.views.send_to_channel")
    def test_patch_karaoke_status_booleans(self, mocked_send_to_channel):
        """Test a manager can modify the karaoke status booleans
        """
        # login as manager
        self.authenticate(self.manager)

        # set can add to playlist to false
        response = self.client.patch(self.url, {"can_add_to_playlist": False})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        karaoke = Karaoke.objects.get_object()
        self.assertFalse(karaoke.can_add_to_playlist)

        # set player play next song to false
        response = self.client.patch(self.url, {"player_play_next_song": False})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        karaoke = Karaoke.objects.get_object()
        self.assertFalse(karaoke.player_play_next_song)

        # set karaoke ongoing to false
        response = self.client.patch(self.url, {"ongoing": False})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        karaoke = Karaoke.objects.get_object()
        self.assertFalse(karaoke.ongoing)
        mocked_send_to_channel.assert_called_with(ANY, "send_idle")

    def test_patch_karaoke_forbidden(self):
        """Test a simple user or an unauthenticated user cannot modify the karaoke
        """
        # login as user
        self.authenticate(self.user)

        # set karaoke ogoing to false
        response = self.client.patch(self.url, {"ongoing": False})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch("playlist.views.send_to_channel")
    def test_patch_ongoing_false(self, mocked_send_to_channel):
        """Test the playlist has been emptied when the kara is not ongoing

        And empty the player errors pool.
        """
        url_player_status = reverse("playlist-player-status")

        # the player is playing
        self.player_play_next_song()

        # there is a player error
        PlayerError.objects.create(
            playlist_entry=self.pe3, error_message="error message"
        )

        # login as manager
        self.authenticate(self.manager)

        # pre-assertion
        # the playlist is not empty
        self.assertTrue(PlaylistEntry.objects.all())

        # the player errors list is not empty
        self.assertTrue(PlayerError.objects.all())

        # the player is currently playing
        response = self.client.get(url_player_status)
        self.assertTrue(response.data["playlist_entry"])

        # set kara ongoing to false
        response = self.client.patch(self.url, {"ongoing": False})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # post-assertion
        # the playlist is empty now
        self.assertFalse(PlaylistEntry.objects.all())

        # the player errors list is empty now
        self.assertFalse(PlayerError.objects.all())

        # the device was requested to be idle
        mocked_send_to_channel.assert_called_with(ANY, "send_idle")

        # the player is not playing anything
        response = self.client.get(url_player_status)
        self.assertFalse(response.data["playlist_entry"])

    def test_put_player_play_next_song_false(self):
        """Test the playlist has not been emptied when can't add to playlist
        """
        url_player_status = reverse("playlist-player-status")

        # the player is playing
        self.player_play_next_song()

        # there is a player error
        PlayerError.objects.create(
            playlist_entry=self.pe3, error_message="error message"
        )

        # login as manager
        self.authenticate(self.manager)

        # pre-assertion
        # the playlist is not empty
        self.assertTrue(PlaylistEntry.objects.all())

        # the player errors list is not empty
        self.assertTrue(PlayerError.objects.all())

        # the player is currently playing
        response = self.client.get(url_player_status)
        self.assertTrue(response.data["playlist_entry"])

        # set can't add to playlist
        response = self.client.put(self.url, {"can_add_to_playlist": False})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # post-assertion
        # the playlist is not empty
        self.assertTrue(PlaylistEntry.objects.all())

        # the player errors list is not empty
        self.assertTrue(PlayerError.objects.all())

        # the player is still playling
        response = self.client.get(url_player_status)
        self.assertTrue(response.data["playlist_entry"])

    @patch("playlist.views.send_to_channel")
    def test_put_resume_kara_player_idle(self, mocked_send_to_channel):
        """Test idle player is requested to play after play next song

        Player play next song was false and the player idle.
        When player play next song switch to true,
        the player should be requested to play the next
        song of the playlist.
        """
        url_player_status = reverse("playlist-player-status")

        # set player play next song to false
        self.set_karaoke(player_play_next_song=False)

        # login as manager
        self.authenticate(self.manager)

        # the player is not currently playing
        response = self.client.get(url_player_status)
        self.assertIsNone(response.data["playlist_entry"])

        # resume the kara
        response = self.client.put(self.url, {"player_play_next_song": True})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # post-assertion
        # the player is requested to start
        mocked_send_to_channel.assert_called_with(
            ANY, "send_playlist_entry", data={"playlist_entry": self.pe1}
        )

    @patch("playlist.views.send_to_channel")
    def test_put_resume_kara_not_idle(self, mocked_send_to_channel):
        """Test not idle player is not requested after play next song

        Player play next song was false and the player not idle.
        When play next song is switched to true,
        the player should not be requested to do anything.
        """
        url_player_status = reverse("playlist-player-status")

        # set player play next song to false
        self.set_karaoke(player_play_next_song=False)

        # the player is playing
        self.player_play_next_song()

        # login as manager
        self.authenticate(self.manager)

        # the player is currently playing
        response = self.client.get(url_player_status)
        self.assertTrue(response.data["playlist_entry"])

        # reset the mock
        mocked_send_to_channel.reset_mock()

        # resume the kara
        response = self.client.put(self.url, {"player_play_next_song": True})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # post-assertion
        # the player is not requested to do anything
        mocked_send_to_channel.assert_not_called()

    @patch("playlist.views.send_to_channel")
    def test_patch_resume_kara_playlist_empty(self, mocked_send_to_channel):
        """Test send_playlist_entry is not sent when there is nothing to play
        """
        url_player_status = reverse("playlist-player-status")

        # login as manager
        self.authenticate(self.manager)

        # empty the playlist
        PlaylistEntry.objects.all().delete()

        # the player is not playing anything
        response = self.client.get(url_player_status)
        self.assertFalse(response.data["playlist_entry"])

        # resume the kara
        response = self.client.put(self.url, {"player_play_next_song": True})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # post-assertion
        # no command was sent to device
        mocked_send_to_channel.assert_not_called()

    @patch("playlist.views.scheduler")
    def test_patch_karaoke_date_stop(self, mocked_scheduler):
        """Test a manager can modify the kara date stop and scheduler is called
        """
        # Mock return value of add_job
        mocked_scheduler.add_job.return_value.id = "job_id"

        # login as manager
        self.authenticate(self.manager)

        # set karaoke date stop
        date_stop = datetime.now(tz)
        response = self.client.patch(self.url, {"date_stop": date_stop.isoformat()})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check karaoke was updated
        karaoke = Karaoke.objects.get_object()
        self.assertEqual(karaoke.date_stop, date_stop)

        # Check job was added
        mocked_scheduler.add_job.assert_called_with(
            clear_date_stop, "date", run_date=date_stop
        )

    @patch("playlist.views.scheduler")
    @patch("playlist.views.cache")
    def test_patch_karaoke_clear_date_stop(self, mocked_cache, mocked_scheduler):
        """Test a manager can clear the kara date stop and job is cancelled
        """
        # set karaoke date stop
        karaoke = Karaoke.objects.get_object()
        date_stop = datetime.now(tz)
        karaoke.date_stop = date_stop
        karaoke.save()

        # login as manager
        self.authenticate(self.manager)

        # clear karaoke date stop
        response = self.client.patch(self.url, {"date_stop": None})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check karaoke was updated
        karaoke = Karaoke.objects.get_object()
        self.assertIsNone(karaoke.date_stop)

        # Check remove was called
        mocked_cache.get.assert_called_with(KARAOKE_JOB_NAME)
        mocked_scheduler.get_job.return_value.remove.assert_called_with()

    @patch("playlist.views.scheduler")
    @patch("playlist.views.cache")
    def test_patch_karaoke_clear_date_stop_existing_job_id(
        self, mocked_cache, mocked_scheduler
    ):
        """Test a manager can clear existing date stop
        """
        # create existing job in cache
        mocked_cache.get.return_value = "job_id"

        # login as manager
        self.authenticate(self.manager)

        # clear karaoke date stop
        response = self.client.patch(self.url, {"date_stop": None})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check remove was called
        mocked_cache.get.assert_called_with(KARAOKE_JOB_NAME)
        mocked_scheduler.get_job.return_value.remove.assert_called_with()
        mocked_cache.delete.assert_not_called()

    @patch("playlist.views.scheduler")
    @patch("playlist.views.cache")
    def test_patch_karaoke_clear_date_stop_existing_job_id_no_job(
        self, mocked_cache, mocked_scheduler
    ):
        """Test a manager can clear existing date stop without job
        """
        # create existing job in cache
        mocked_cache.get.return_value = "job_id"
        mocked_scheduler.get_job.return_value = None

        # login as manager
        self.authenticate(self.manager)

        # clear karaoke date stop
        response = self.client.patch(self.url, {"date_stop": None})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check remove was called
        mocked_cache.get.assert_called_with(KARAOKE_JOB_NAME)
        mocked_cache.delete.assert_called_with(KARAOKE_JOB_NAME)
