from datetime import datetime

from django.utils import timezone
from django.core.urlresolvers import reverse
from django.utils.dateparse import parse_datetime
from rest_framework import status

from .base_test import BaseAPITestCase
from .models import Karaoke, PlaylistEntry

tz = timezone.get_default_timezone()


class KaraokeViewRetrieveUpdateAPIViewTestCase(BaseAPITestCase):
    url = reverse('playlist-karaoke')
    url_digest = reverse('playlist-digest')

    def setUp(self):
        self.create_test_data()

    def test_get_karaoke(self):
        """Test an authenticated user can access the kara status
        """
        # set stop date
        karaoke = Karaoke.get_object()
        date_stop = datetime.now(tz)
        karaoke.date_stop = date_stop
        karaoke.save()

        # login as simple user
        self.authenticate(self.user)

        # get kara status
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], Karaoke.PLAY)
        self.assertEqual(parse_datetime(response.data['date_stop']),
                         date_stop)

        # Get kara status again but through digest route
        response = self.client.get(self.url_digest)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data['karaoke']['status'],
            Karaoke.PLAY)

    def test_get_karaoke_forbidden(self):
        """Test an unauthenticated user cannot access the kara status
        """
        # get kara status
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_patch_karaoke_status(self):
        """Test a manager can modify the kara status
        """
        # login as manager
        self.authenticate(self.manager)

        # set kara status
        response = self.client.patch(self.url, {'status': Karaoke.PAUSE})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        karaoke = Karaoke.get_object()
        self.assertEqual(karaoke.status, Karaoke.PAUSE)

    def test_patch_karaoke_forbidden(self):
        """Test a simple user or an unauthenticated user cannot modify the kara
        status
        """
        # login as user
        self.authenticate(self.user)

        # set kara status
        response = self.client.patch(self.url, {'status': Karaoke.PAUSE})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_patch_karaoke_status_stop(self):
        """Test the playlist has been emptied when the kara is stopped
        """
        url_player_status = reverse('playlist-player-status')

        # the player is playing
        self.player_play_next_song()

        # login as manager
        self.authenticate(self.manager)

        # pre-assertion
        # the playlist is not empty
        self.assertTrue(PlaylistEntry.objects.all())

        # the player is currently playing
        response = self.client.get(url_player_status)
        self.assertTrue(response.data['playlist_entry'])

        # stop the kara
        response = self.client.patch(self.url, {'status': Karaoke.STOP})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # post-assertion
        # the playlist is empty now
        self.assertFalse(PlaylistEntry.objects.all())

        # the player is not playing anything
        response = self.client.get(url_player_status)
        self.assertFalse(response.data['playlist_entry'])

    def test_patch_karaoke_date_stop(self):
        """Test a manager can modify the kara date stop
        """
        # login as manager
        self.authenticate(self.manager)

        # set kara status
        date_stop = datetime.now(tz)
        response = self.client.patch(self.url, {'date_stop':
                                                date_stop.isoformat()})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        karaoke = Karaoke.get_object()
        self.assertEqual(karaoke.date_stop, date_stop)
