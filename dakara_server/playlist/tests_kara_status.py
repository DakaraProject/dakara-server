from django.core.urlresolvers import reverse
from rest_framework import status

from .base_test import BaseAPITestCase
from .models import KaraStatus, PlaylistEntry, PlayerError


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

    def test_put_kara_status_stop(self):
        """Test the playlist has been emptied when the kara is stopped
        """
        url_player_status = reverse('playlist-player-status')

        # the player is playing
        self.player_play_next_song()

        # there is a player error
        PlayerError.objects.create(
            playlist_entry=self.pe1,
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

        # the player is not playing anything
        response = self.client.get(url_player_status)
        self.assertFalse(response.data['playlist_entry'])
