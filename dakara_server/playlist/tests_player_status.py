from unittest.mock import patch
from datetime import datetime, timedelta

from django.core.urlresolvers import reverse
from django.utils.dateparse import parse_datetime
from rest_framework import status

from playlist.base_test import BaseAPITestCase, tz
from playlist.models import Player, PlaylistEntry


class PlayerStatusViewTestCase(BaseAPITestCase):
    """Test the view of the player"""
    url = reverse('playlist-player-status')

    def setUp(self):
        self.create_test_data()

    def test_get_status_idle(self):
        """Test to access the player status when idle"""
        self.authenticate(self.user)

        # check the player is idle
        player = Player.get_or_create()
        player.save()
        self.assertIsNone(player.playlist_entry)

        # assert the status of the player
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data['playlist_entry'])
        self.assertEqual(response.data['timing'], 0)
        self.assertFalse(response.data['paused'])
        self.assertEqual(parse_datetime(response.data['date']), player.date)

    def test_get_status_in_transition(self):
        """Test to access the player status when in transition"""
        self.authenticate(self.user)

        # set the player in transition
        player = self.player_play_next_song(in_transition=True)

        # assert the status of the player
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['playlist_entry']['id'], self.pe1.id)
        self.assertTrue(response.data['in_transition'])
        self.assertEqual(response.data['timing'], 0)
        self.assertFalse(response.data['paused'])
        self.assertEqual(parse_datetime(response.data['date']), player.date)

    def test_get_status_in_play_with_timing(self):
        """Test to access the player status when in play with timing"""
        self.authenticate(self.user)

        # set the player in play
        player = self.player_play_next_song(timing=timedelta(seconds=2))

        # assert the status of the player
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['playlist_entry']['id'], self.pe1.id)
        self.assertFalse(response.data['in_transition'])
        self.assertEqual(response.data['timing'], 2)
        self.assertFalse(response.data['paused'])
        self.assertEqual(parse_datetime(response.data['date']), player.date)

    def test_get_status_in_pause_with_timing(self):
        """Test to access the player status when in pause with timing"""
        self.authenticate(self.user)

        # set the player in play
        player = self.player_play_next_song(timing=timedelta(seconds=5),
                                            paused=True)

        # assert the status of the player
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['playlist_entry']['id'], self.pe1.id)
        self.assertFalse(response.data['in_transition'])
        self.assertEqual(response.data['timing'], 5)
        self.assertTrue(response.data['paused'])
        self.assertEqual(parse_datetime(response.data['date']), player.date)

    def test_get_status_forbidden(self):
        """Test to access the player status when not loged in"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch('playlist.views.broadcast_to_channel')
    @patch('playlist.models.datetime',
           side_effect=lambda *args, **kwargs: datetime(*args, **kwargs))
    def test_put_status_idle(self, mocked_datetime,
                             mocked_broadcast_to_channel):
        """Test to set the player idle"""
        self.authenticate(self.player)

        # patch the now method
        now = datetime.now(tz)
        mocked_datetime.now.return_value = now

        # set the player already idle
        player = Player.get_or_create()
        player.save()

        # perform the request
        response = self.client.patch(self.url, data={
            'playlist_entry_id': None,
            'paused': False,
            'timing': 0,
            'in_transition': False,
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # assert the response
        self.assertIsNone(response.data['playlist_entry'])
        self.assertFalse(response.data['paused'])
        self.assertFalse(response.data['in_transition'])
        self.assertEqual(response.data['timing'], 0)

        # assert the result
        player = Player.get_or_create()
        self.assertIsNone(player.playlist_entry)
        self.assertFalse(player.paused)
        self.assertEqual(player.timing, timedelta(0))
        self.assertFalse(player.in_transition)
        self.assertEqual(player.date, now)

        # assert an event has been broadcasted to the front
        mocked_broadcast_to_channel.assert_called_with(
            'playlist.front', 'send_player_status', {'player': player}
        )

    @patch('playlist.views.broadcast_to_channel')
    @patch('playlist.models.datetime',
           side_effect=lambda *args, **kwargs: datetime(*args, **kwargs))
    def test_put_status_in_transition(self, mocked_datetime,
                                      mocked_broadcast_to_channel):
        """Test to set the player in transition"""
        self.authenticate(self.player)

        # patch the now method
        now = datetime.now(tz)
        mocked_datetime.now.return_value = now

        # set the player already in transition
        self.player_play_next_song(in_transition=True)

        # perform the request
        response = self.client.put(self.url, data={
            'playlist_entry_id': self.pe1.id,
            'paused': False,
            'timing': 0,
            'in_transition': True,
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # assert the response
        self.assertEqual(response.data['playlist_entry']['id'], self.pe1.id)
        self.assertFalse(response.data['paused'])
        self.assertTrue(response.data['in_transition'])
        self.assertEqual(response.data['timing'], 0)

        # assert the result
        player = Player.get_or_create()
        self.assertEqual(player.playlist_entry, self.pe1)
        self.assertFalse(player.paused)
        self.assertEqual(player.timing, timedelta(0))
        self.assertTrue(player.in_transition)
        self.assertEqual(player.date, now)

        # assert an event has been broadcasted to the front
        mocked_broadcast_to_channel.assert_called_with(
            'playlist.front', 'send_player_status', {'player': player}
        )

    def test_put_status_in_transition_with_timing(self):
        """Test to set the player in transition with a timing

        This case is invalid, the timing won't be stored."""
        self.authenticate(self.player)

        # set the player already in transition
        player = self.player_play_next_song(in_transition=True)
        self.assertEqual(player.timing, timedelta(0))

        # perform the request
        response = self.client.put(self.url, data={
            'playlist_entry_id': self.pe1.id,
            'paused': False,
            'timing': 2,
            'in_transition': True,
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # assert the response
        self.assertEqual(response.data['playlist_entry']['id'], self.pe1.id)
        self.assertFalse(response.data['paused'])
        self.assertTrue(response.data['in_transition'])
        self.assertEqual(response.data['timing'], 0)

        # assert the result
        player = Player.get_or_create()
        self.assertEqual(player.timing, timedelta(0))

    @patch('playlist.views.broadcast_to_channel')
    @patch('playlist.models.datetime',
           side_effect=lambda *args, **kwargs: datetime(*args, **kwargs))
    def test_put_status_not_in_transition(self, mocked_datetime,
                                          mocked_broadcast_to_channel):
        """Test to set the player not in transition anymore (full update)"""
        self.authenticate(self.player)

        # patch the now method
        now = datetime.now(tz)
        mocked_datetime.now.return_value = now

        # set the player in transition
        self.player_play_next_song(in_transition=True)

        # perform the request
        response = self.client.put(self.url, data={
            'playlist_entry_id': self.pe1.id,
            'paused': False,
            'timing': 0,
            'in_transition': False,
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # assert the response
        self.assertEqual(response.data['playlist_entry']['id'], self.pe1.id)
        self.assertFalse(response.data['paused'])
        self.assertFalse(response.data['in_transition'])
        self.assertEqual(response.data['timing'], 0)

        # assert the result
        player = Player.get_or_create()
        self.assertEqual(player.playlist_entry, self.pe1)
        self.assertFalse(player.paused)
        self.assertEqual(player.timing, timedelta(0))
        self.assertFalse(player.in_transition)
        self.assertEqual(player.date, now)

        # assert an event has been broadcasted to the front
        mocked_broadcast_to_channel.assert_called_with(
            'playlist.front', 'send_player_status', {'player': player}
        )

    @patch('playlist.views.broadcast_to_channel')
    @patch('playlist.models.datetime',
           side_effect=lambda *args, **kwargs: datetime(*args, **kwargs))
    def test_patch_status_not_in_transition(self, mocked_datetime,
                                            mocked_broadcast_to_channel):
        """Test to set the player not in transition anymore (partial update)"""
        self.authenticate(self.player)

        # patch the now method
        now = datetime.now(tz)
        mocked_datetime.now.return_value = now

        # set the player in transition
        self.player_play_next_song(in_transition=True)

        # perform the request
        response = self.client.patch(self.url, data={
            'playlist_entry_id': self.pe1.id,
            'in_transition': False,
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # assert the response
        self.assertEqual(response.data['playlist_entry']['id'], self.pe1.id)
        self.assertFalse(response.data['paused'])
        self.assertFalse(response.data['in_transition'])
        self.assertEqual(response.data['timing'], 0)

        # assert the result
        player = Player.get_or_create()
        self.assertEqual(player.playlist_entry, self.pe1)
        self.assertFalse(player.paused)
        self.assertEqual(player.timing, timedelta(0))
        self.assertFalse(player.in_transition)
        self.assertEqual(player.date, now)

        # assert an event has been broadcasted to the front
        mocked_broadcast_to_channel.assert_called_with(
            'playlist.front', 'send_player_status', {'player': player}
        )

    @patch('playlist.views.broadcast_to_channel')
    @patch('playlist.models.datetime',
           side_effect=lambda *args, **kwargs: datetime(*args, **kwargs))
    def test_put_status_in_play_with_timing(self, mocked_datetime,
                                            mocked_broadcast_to_channel):
        """Test to set the player in play with a timing"""
        self.authenticate(self.player)

        # patch the now method
        now = datetime.now(tz)
        mocked_datetime.now.return_value = now

        # set the player already in play
        self.player_play_next_song(timing=timedelta(seconds=1))

        # perform the request
        response = self.client.put(self.url, data={
            'playlist_entry_id': self.pe1.id,
            'paused': False,
            'timing': 2,
            'in_transition': False,
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # assert the response
        self.assertEqual(response.data['playlist_entry']['id'], self.pe1.id)
        self.assertFalse(response.data['paused'])
        self.assertFalse(response.data['in_transition'])
        self.assertEqual(response.data['timing'], 2)

        # assert the result
        player = Player.get_or_create()
        self.assertEqual(player.playlist_entry, self.pe1)
        self.assertFalse(player.paused)
        self.assertEqual(player.timing, timedelta(seconds=2))
        self.assertFalse(player.in_transition)
        self.assertEqual(player.date, now)
        self.assertFalse(hasattr(player, 'finished'))

        # assert an event has been broadcasted to the front
        mocked_broadcast_to_channel.assert_called_with(
            'playlist.front', 'send_player_status', {'player': player}
        )

    @patch('playlist.views.broadcast_to_channel')
    @patch('playlist.models.datetime',
           side_effect=lambda *args, **kwargs: datetime(*args, **kwargs))
    def test_put_status_in_pause_with_timing(self, mocked_datetime,
                                             mocked_broadcast_to_channel):
        """Test to set the player in pause with a timing"""
        self.authenticate(self.player)

        # patch the now method
        now = datetime.now(tz)
        mocked_datetime.now.return_value = now

        # set the player in play
        self.player_play_next_song(timing=timedelta(seconds=1))

        # perform the request
        response = self.client.put(self.url, data={
            'playlist_entry_id': self.pe1.id,
            'paused': True,
            'timing': 2,
            'in_transition': False,
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # assert the response
        self.assertEqual(response.data['playlist_entry']['id'], self.pe1.id)
        self.assertTrue(response.data['paused'])
        self.assertFalse(response.data['in_transition'])
        self.assertEqual(response.data['timing'], 2)

        # assert the result
        player = Player.get_or_create()
        self.assertEqual(player.playlist_entry, self.pe1)
        self.assertTrue(player.paused)
        self.assertEqual(player.timing, timedelta(seconds=2))
        self.assertFalse(player.in_transition)
        self.assertEqual(player.date, now)

        # assert an event has been broadcasted to the front
        mocked_broadcast_to_channel.assert_called_with(
            'playlist.front', 'send_player_status', {'player': player}
        )

    @patch('playlist.views.broadcast_to_channel')
    def test_patch_status_song_finished(self, mocked_broadcast_to_channel):
        """Test to set the player when a songs finishes"""
        self.authenticate(self.player)

        # set the player in play
        self.player_play_next_song()

        # pre assert
        pe1 = PlaylistEntry.objects.get(pk=self.pe1.id)
        self.assertFalse(pe1.was_played)

        # perform the request
        response = self.client.patch(self.url, data={
            'playlist_entry_id': self.pe1.id,
            'finished': True
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # assert the player has not changed
        player = Player.get_or_create()
        self.assertIsNone(player.playlist_entry)
        self.assertFalse(hasattr(player, 'finished'))

        # assert the response
        self.assertIsNone(response.data['playlist_entry'])
        self.assertFalse(response.data['paused'])
        self.assertFalse(response.data['in_transition'])
        self.assertEqual(response.data['timing'], 0)

        # assert the result
        pe1 = PlaylistEntry.objects.get(pk=self.pe1.id)
        self.assertTrue(pe1.was_played)

        # assert an event has been broadcasted to the device
        mocked_broadcast_to_channel.assert_called_with(
            'playlist.device', 'handle_next'
        )

    def test_put_status_failed_wrong_playlist_entry(self):
        """Test to set the player status with another playlist entry"""
        self.authenticate(self.player)

        # set the player already in play
        player_old = self.player_play_next_song(timing=timedelta(seconds=1))

        # perform the request
        response = self.client.put(self.url, data={
            'playlist_entry_id': self.pe2.id,
            'paused': False,
            'timing': 2,
            'in_transition': False,
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # assert the result
        player_new = Player.get_or_create()
        self.assertEqual(player_old, player_new)

    def test_put_status_forbidden_not_authenticated(self):
        """Test to set the player when not authenticated"""
        response = self.client.put(self.url, data={
            'playlist_entry_id': self.pe1.id,
            'paused': False,
            'timing': 2,
            'in_transition': False,
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_put_status_forbidden_not_player(self):
        """Test to set the player when not a player user"""
        self.authenticate(self.user)
        response = self.client.put(self.url, data={
            'playlist_entry_id': self.pe1.id,
            'paused': False,
            'timing': 2,
            'in_transition': False,
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
