from django.core.urlresolvers import reverse
from rest_framework import status
from .base_test import BaseAPITestCase

class PlayerStatusViewAPIViewTestCase(BaseAPITestCase):
    url = reverse('playlist-player-status')
    url_aggregated = reverse('playlist-player')

    def setUp(self):
        self.create_test_data()

    def test_get_player_status(self):
        """
        Test to verify player status when nothing is playing
        """
        # Login as simple user 
        self.authenticate(self.user)

        # Get player status
        # Should be default player state
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['playlist_entry'], None)
        self.assertEqual(response.data['timing'], 0)
        self.assertEqual(response.data['paused'], False)

        # Get player status again but through aggregated route
        response = self.client.get(self.url_aggregated)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status']['playlist_entry'], None)
        self.assertEqual(response.data['status']['timing'], 0)
        self.assertEqual(response.data['status']['paused'], False)

    def test_get_player_status_playing(self):
        """
        Test to verify player status when playing
        """
        # Make player play next song in playlist at 23 seconds
        playing_time = 23
        self.player_play_next_song(playing_time)

        # Login as simple user 
        self.authenticate(self.user)

        # Get player status
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['playlist_entry']['id'], self.pe1.id)
        self.assertEqual(response.data['timing'], playing_time)
        self.assertEqual(response.data['paused'], False)

        # Get player status again but through aggregated route
        response = self.client.get(self.url_aggregated)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status']['playlist_entry']['id'], self.pe1.id)
        self.assertEqual(response.data['status']['timing'], playing_time)
        self.assertEqual(response.data['status']['paused'], False)

        # Make player continue playing the song, but at 47 seconds and paused
        playing_time = 47
        self.player_play_song(self.pe1.id, playing_time, True)

        # Login as simple user
        self.authenticate(self.user)

        # Get player status
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['playlist_entry']['id'], self.pe1.id)
        self.assertEqual(response.data['timing'], playing_time)
        self.assertEqual(response.data['paused'], True)

        # Get player status again but through aggregated route
        response = self.client.get(self.url_aggregated)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status']['playlist_entry']['id'], self.pe1.id)
        self.assertEqual(response.data['status']['timing'], playing_time)
        self.assertEqual(response.data['status']['paused'], True)

        # Make player play next song in playlist at 2 seconds
        playing_time = 2
        self.player_play_next_song(playing_time)

        # Login as simple user 
        self.authenticate(self.user)

        # Get player status
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['playlist_entry']['id'], self.pe2.id)
        self.assertEqual(response.data['timing'], playing_time)
        self.assertEqual(response.data['paused'], False)

        # Get player status again but through aggregated route
        response = self.client.get(self.url_aggregated)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status']['playlist_entry']['id'], self.pe2.id)
        self.assertEqual(response.data['status']['timing'], playing_time)
        self.assertEqual(response.data['status']['paused'], False)

        # No more song in playlist, player should be idle
        playing_time = 0
        self.player_play_next_song(playing_time)

        # Login as simple user 
        self.authenticate(self.user)

        # Get player status
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['playlist_entry'], None)
        self.assertEqual(response.data['timing'], playing_time)
        self.assertEqual(response.data['paused'], False)

        # Get player status again but through aggregated route
        response = self.client.get(self.url_aggregated)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status']['playlist_entry'], None)
        self.assertEqual(response.data['status']['timing'], playing_time)
        self.assertEqual(response.data['status']['paused'], False)


class PlayerManageViewAPIViewTestCase(BaseAPITestCase):
    url = reverse('playlist-player-manage')
    url_aggregated = reverse('playlist-player')

    def setUp(self):
        self.create_test_data()

    def test_set_player_pause(self):
        """
        Test to test pausing player
        """
        # Play next song and check the player does not receive pause command
        response = self.player_play_next_song()
        self.assertEqual(response.data['pause'], False)
        self.assertEqual(response.data['skip'], False)

        # Login as manager
        self.authenticate(self.manager)

        # Get current commands
        # Should be default
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['pause'], False)
        self.assertEqual(response.data['skip'], False)

        # Get player commands again but through aggregated route
        response = self.client.get(self.url_aggregated)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['manage']['pause'], False)
        self.assertEqual(response.data['manage']['skip'], False)

        # Request pause
        response = self.client.put(self.url,
                {
                    'pause': True,
                    'skip': False
                }
            )
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

        # Get current commands
        # Should be pause requested
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['pause'], True)
        self.assertEqual(response.data['skip'], False)

        # Get player commands again but through aggregated route
        response = self.client.get(self.url_aggregated)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['manage']['pause'], True)
        self.assertEqual(response.data['manage']['skip'], False)


        # Now, check player receive the pause request
        response = self.player_play_next_song()
        self.assertEqual(response.data['pause'], True)
        self.assertEqual(response.data['skip'], False)

    def test_set_player_pause_manager(self):
        """
        Test to test pausing player as manager
        """
        # Play next song
        self.player_play_next_song()

        # Login as manager
        self.authenticate(self.manager)

        # Request pause
        # able to pause own entry
        response = self.client.put(self.url,
                {
                    'pause': True,
                    'skip': False
                }
            )
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

        # Play next song
        self.player_play_next_song()

        # Login as manager
        self.authenticate(self.manager)

        # Request pause
        # able to pause other's entry
        response = self.client.put(self.url,
                {
                    'pause': True,
                    'skip': False
                }
            )
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

    def test_set_player_pause_user(self):
        """
        Test to test pausing player as user
        """
        # Play next song
        self.player_play_next_song()

        # Login as playlist user
        self.authenticate(self.p_user)

        # Request pause
        # not able to pause other's entry
        response = self.client.put(self.url,
                {
                    'pause': True,
                    'skip': False
                }
            )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Play next song
        self.player_play_next_song()

        # Login as playlist user
        self.authenticate(self.p_user)

        # Request pause
        # able to pause own entry
        response = self.client.put(self.url,
                {
                    'pause': True,
                    'skip': False
                }
            )
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

    def test_set_player_skip(self):
        """
        Test to test skiping
        """
        # Play next song and check the player does not receive skip command
        response = self.player_play_next_song()
        self.assertEqual(response.data['pause'], False)
        self.assertEqual(response.data['skip'], False)

        # Login as manager
        self.authenticate(self.manager)

        # Get current commands
        # Should be default
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['pause'], False)
        self.assertEqual(response.data['skip'], False)

        # Get player commands again but through aggregated route
        response = self.client.get(self.url_aggregated)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['manage']['pause'], False)
        self.assertEqual(response.data['manage']['skip'], False)

        # Request skip
        response = self.client.put(self.url,
                {
                    'pause': False,
                    'skip': True
                }
            )
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

        # Get current commands
        # Should be skip requested
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['pause'], False)
        self.assertEqual(response.data['skip'], True)

        # Get player commands again but through aggregated route
        response = self.client.get(self.url_aggregated)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['manage']['pause'], False)
        self.assertEqual(response.data['manage']['skip'], True)


        # Now, player is still playing the same song,
        # server should send skip request
        response = self.player_play_song(self.pe1.id)
        self.assertEqual(response.data['pause'], False)
        self.assertEqual(response.data['skip'], True)

        # Player now plays next song, skip flag should be reset
        response = self.player_play_next_song()
        self.assertEqual(response.data['pause'], False)
        self.assertEqual(response.data['skip'], False)


# TODO: Player errors check
class PlayerErrorsPoolViewAPIViewTestCase(BaseAPITestCase):
    url = reverse('playlist-player-errors')
    url_aggregated = reverse('playlist-player')

    def setUp(self):
        self.create_test_data()

    def test_get_player_errors(self):
        """
        Test to test player errrors
        """
        # Login as simple user
        self.authenticate(self.user)

        # Get player errrors
        # Should not have any
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

        # Get player errors again but through aggregated route
        response = self.client.get(self.url_aggregated)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['errors']), 0)

        # Simulate player sending and error
        error_message = "Testing Errors from the player"
        self.player_send_error(self.pe1.id, error_message)

        # Login as simple user
        self.authenticate(self.user)

        # Get player errors
        # Should have one error
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        error = response.data[0]
        self.assertIsNotNone(error.get('id'))
        self.assertEqual(error['song']['id'], self.song1.id)
        self.assertEqual(error['error_message'], error_message)

        # Get player errors again but through aggregated route
        response = self.client.get(self.url_aggregated)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['errors']), 1)
        error = response.data['errors'][0]
        self.assertIsNotNone(error.get('id'))
        self.assertEqual(error['song']['id'], self.song1.id)
        self.assertEqual(error['error_message'], error_message)
