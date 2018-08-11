from unittest.mock import patch

from django.core.urlresolvers import reverse
from rest_framework import status

from playlist.base_test import BaseAPITestCase
from playlist.models import KaraStatus, PlaylistEntry, PlayerError


class KaraStatusViewRetrieveUpdateAPIViewTestCase(BaseAPITestCase):
    url = reverse('playlist-kara-status')
    url_digest = reverse('playlist-digest')

    def setUp(self):
        self.create_test_data()

    def test_get_kara_status(self):
        """Test an authenticated user can access the kara status
        """
        # login as simple user
        self.authenticate(self.user)

        # get kara status
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], KaraStatus.PLAY)

        # Get kara status again but through digest route
        response = self.client.get(self.url_digest)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data['kara_status']['status'],
            KaraStatus.PLAY)

    def test_get_kara_status_forbidden(self):
        """Test an unauthenticated user cannot access the kara status
        """
        # get kara status
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_put_kara_status(self):
        """Test a manager can modify the kara status
        """
        # login as manager
        self.authenticate(self.manager)

        # set kara status
        response = self.client.put(self.url, {'status': KaraStatus.PAUSE})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        kara_status = KaraStatus.objects.first()
        self.assertEqual(kara_status.status, KaraStatus.PAUSE)

    def test_put_kara_status_forbidden(self):
        """Test a simple user or an unauthenticated user cannot modify the kara
        status
        """
        # login as user
        self.authenticate(self.user)

        # set kara status
        response = self.client.put(self.url, {'status': KaraStatus.PAUSE})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch('playlist.views.broadcast_to_channel')
    def test_put_kara_status_stop(self, mocked_broadcast_to_channel):
        """Test the playlist has been emptied when the kara is stopped
        """
        url_player_status = reverse('playlist-player-status')

        # the player is playing
        self.player_play_next_song()

        # there is a player error
        PlayerError.objects.create(
            playlist_entry=self.pe3,
            error_message="error message"
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
        self.assertTrue(response.data['playlist_entry'])

        # stop the kara
        response = self.client.put(self.url, {'status': KaraStatus.STOP})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # post-assertion
        # the playlist is empty now
        self.assertFalse(PlaylistEntry.objects.all())

        # the player errors list is empty now
        self.assertFalse(PlayerError.objects.all())

        # the device was requested to be idle
        mocked_broadcast_to_channel.assert_called_with('playlist.device',
                                                       'send_idle')

        # the player is not playing anything
        response = self.client.get(url_player_status)
        self.assertFalse(response.data['playlist_entry'])

    def test_put_kara_status_pause(self):
        """Test the playlist has not been emptied when the kara is paused
        """
        url_player_status = reverse('playlist-player-status')

        # the player is playing
        self.player_play_next_song()

        # there is a player error
        PlayerError.objects.create(
            playlist_entry=self.pe3,
            error_message="error message"
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
        self.assertTrue(response.data['playlist_entry'])

        # pause the kara
        response = self.client.put(self.url, {'status': KaraStatus.PAUSE})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # post-assertion
        # the playlist is not empty
        self.assertTrue(PlaylistEntry.objects.all())

        # the player errors list is not empty
        self.assertTrue(PlayerError.objects.all())

        # the player is still playling
        response = self.client.get(url_player_status)
        self.assertTrue(response.data['playlist_entry'])

    @patch('playlist.views.broadcast_to_channel')
    def test_put_kara_status_play_player_idle(self,
                                              mocked_broadcast_to_channel):
        """Test idle player is requested to play after kara status is play

        The kara status was paused and the player idle. When the kara status
        is switched to play, the player should be requested to play the next
        song of the playlist.
        """
        url_player_status = reverse('playlist-player-status')

        # set the kara status to pause
        kara_status = KaraStatus.get_object()
        kara_status.status = KaraStatus.PAUSE
        kara_status.save()

        # login as manager
        self.authenticate(self.manager)

        # the player is not currently playing
        response = self.client.get(url_player_status)
        self.assertIsNone(response.data['playlist_entry'])

        # resume the kara
        response = self.client.put(self.url, {'status': KaraStatus.PLAY})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # post-assertion
        # the player is requested to start
        mocked_broadcast_to_channel.assert_called_with(
            'playlist.device', 'send_playlist_entry', data={
                'playlist_entry': self.pe1
            }
        )

    @patch('playlist.views.broadcast_to_channel')
    def test_put_kara_status_play_player_not_idle(self,
                                                  mocked_broadcast_to_channel):
        """Test not idle player is not requested after kara status is play

        The kara status was paused and the player not idle. When the kara
        status is switched to play, the player should not be requested to do
        anything.
        """
        url_player_status = reverse('playlist-player-status')

        # set the kara status to pause
        kara_status = KaraStatus.get_object()
        kara_status.status = KaraStatus.PAUSE
        kara_status.save()

        # the player is playing
        self.player_play_next_song()

        # login as manager
        self.authenticate(self.manager)

        # the player is currently playing
        response = self.client.get(url_player_status)
        self.assertTrue(response.data['playlist_entry'])

        # reset the mock
        mocked_broadcast_to_channel.reset_mock()

        # resume the kara
        response = self.client.put(self.url, {'status': KaraStatus.PLAY})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # post-assertion
        # the player is not requested to do anything
        mocked_broadcast_to_channel.assert_not_called()
