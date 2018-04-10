import logging
from datetime import datetime, timedelta
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.core.cache import cache
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase
from rest_framework import status

from library.models import Song, SongTag
from .models import PlaylistEntry, KaraStatus


UserModel = get_user_model()


logging.disable(logging.CRITICAL)


class BaseAPITestCase(APITestCase):

    def tearDown(self):
        # Clear cache between tests, so that stored player state is re-init
        cache.clear()

    def authenticate(self, user):
        token, created = Token.objects.get_or_create(user=user)

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

    def create_user(self, username, playlist_level=None, library_level=None, users_level=None):
        user = UserModel.objects.create_user(username, "", "password")
        user.playlist_permission_level = playlist_level
        user.library_permission_level = library_level
        user.users_permission_level = users_level
        user.save()
        return user

    def create_test_data(self):
        """
        Create test users songs, and playlist entries
        """
        # create a user without any rights
        self.user = self.create_user("TestUser")

        # create a playlist user
        self.p_user = self.create_user("TestPlaylistUser", playlist_level="u")

        # create a playlist manager
        self.manager = self.create_user("testPlaylistManager", playlist_level="m")

        # create a player
        self.player = self.create_user("testPlayer", playlist_level="p")

        # Create tags
        self.tag1 = SongTag(name='TAG1')
        self.tag1.save()

        # Create songs
        self.song1 = Song(title="Song1")
        self.song1.save()
        self.song1.tags.add(self.tag1)
        self.song2 = Song(title="Song2")
        self.song2.save()

        # Create playlist entries
        self.pe1 = PlaylistEntry(song=self.song1, owner=self.manager)
        self.pe1.save()

        self.pe2 = PlaylistEntry(song=self.song2, owner=self.p_user)
        self.pe2.save()

        self.pe3 = PlaylistEntry(
                song=self.song2,
                owner=self.manager,
                was_played=True,
                date_played=datetime.now()
                )
        self.pe3.save()

        self.pe4 = PlaylistEntry(
                song=self.song1,
                owner=self.user,
                was_played=True,
                date_played=datetime.now() - timedelta(minutes=15)
                )
        self.pe4.save()

        # Set kara status in play mode
        kara_status = KaraStatus.get_object()
        kara_status.status = KaraStatus.PLAY
        kara_status.save()

    @staticmethod
    def set_kara_status_stop():
        kara_status = KaraStatus.get_object()
        kara_status.status = KaraStatus.STOP
        kara_status.save()

    @staticmethod
    def set_kara_status_pause():
        kara_status = KaraStatus.get_object()
        kara_status.status = KaraStatus.PAUSE
        kara_status.save()

    def check_playlist_entry_json(self, json, expected_entry):
        """
        Method to check a representation against expected playlist entry
        """
        self.assertEqual(json['id'], expected_entry.id)
        self.assertEqual(json['owner']['id'], expected_entry.owner.id)
        self.assertEqual(json['song']['id'], expected_entry.song.id)

    def check_playlist_played_entry_json(self, json, expected_entry):
        """
        Method to check a representation against expected playlist played entry
        """
        self.check_playlist_entry_json(json, expected_entry)
        self.assertEqual(datetime.strptime(json['date_played'], "%Y-%m-%dT%H:%M:%S.%fZ"), expected_entry.date_played)

    def player_play_next_song(self, time=0, paused=False):
        """
        Simulate player playing the next song at given time
        Return pause/skip commands directed toward the player
        """
        url = reverse('playlist-device-status')
        # Login as player
        self.authenticate(self.player)

        # Get next song to play
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        next_id = response.data.get('id')

        return self.player_play_song(next_id, time, paused)


    def player_play_song(self, playlist_entry_id, time=0, paused=False):
        """
        Simulate the player reporting playing the specified song
        for the given time and pause status
        """
        url = reverse('playlist-device-status')
        # Login as player
        self.authenticate(self.player)
        # Put as if playing next song
        response = self.client.put(url,
                {
                    'playlist_entry_id': playlist_entry_id,
                    'timing': time,
                    'paused': paused
                }
            )
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

        return response

    def player_send_error(self, playlist_entry_id, message):
        """
        Simulate the player reporting an error
        """
        url = reverse('playlist-device-error')
        # Login as player
        self.authenticate(self.player)
        # Put as if playing next song
        response = self.client.post(url,
                {
                    'playlist_entry': playlist_entry_id,
                    'error_message': message,
                }
            )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
