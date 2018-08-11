import logging
from datetime import datetime, timedelta
import inspect

from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.core.cache import cache
from django.utils.dateparse import parse_datetime
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase
from rest_framework import status

from library.models import Song, SongTag
from playlist.models import PlaylistEntry, KaraStatus, Player

UserModel = get_user_model()
tz = timezone.get_default_timezone()


class Provider:
    """Provides helper functions for tests
    """
    def authenticate(self, user):
        """Authenticate against the provided user
        """
        token, _ = Token.objects.get_or_create(user=user)

        return token

    @staticmethod
    def create_user(username, playlist_level=None,
                    library_level=None, users_level=None):
        """Create a user with the provided permissions
        """
        user = UserModel.objects.create_user(username, "", "password")
        user.playlist_permission_level = playlist_level
        user.library_permission_level = library_level
        user.users_permission_level = users_level
        user.save()
        return user

    def create_test_data(self):
        """Create test users songs, and playlist entries
        """
        # create a user without any rights
        self.user = self.create_user("TestUser")

        # create a playlist user
        self.p_user = self.create_user("TestPlaylistUser",
                                       playlist_level=UserModel.USER)

        # create a playlist manager
        self.manager = self.create_user("testPlaylistManager",
                                        playlist_level=UserModel.MANAGER)

        # create a player
        self.player = self.create_user("testPlayer",
                                       playlist_level=UserModel.PLAYER)

        # Create tags
        self.tag1 = SongTag(name='TAG1')
        self.tag1.save()

        # Create songs
        self.song1 = Song(title="Song1", duration=timedelta(seconds=5))
        self.song1.save()
        self.song1.tags.add(self.tag1)
        self.song2 = Song(title="Song2", duration=timedelta(seconds=10))
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
            date_played=datetime.now(tz)
        )
        self.pe3.save()

        self.pe4 = PlaylistEntry(
            song=self.song1,
            owner=self.user,
            was_played=True,
            date_played=datetime.now(tz) - timedelta(minutes=15)
        )
        self.pe4.save()

        # Set kara status in play mode
        kara_status = KaraStatus.get_object()
        kara_status.status = KaraStatus.PLAY
        kara_status.save()

    @staticmethod
    def set_kara_status_stop():
        """Put the karaoke in stop state
        """
        kara_status = KaraStatus.get_object()
        kara_status.status = KaraStatus.STOP
        kara_status.save()

    @staticmethod
    def set_kara_status_pause():
        """Put the karaoke in pause state
        """
        kara_status = KaraStatus.get_object()
        kara_status.status = KaraStatus.PAUSE
        kara_status.save()

    def player_play_next_song(self, *args, **kwargs):
        """Set the player playing the next song
        """
        # get current entry
        current_entry = PlaylistEntry.get_playing()

        if current_entry is not None:
            # set current entry as played
            current_entry.set_finished()

        # get next entry
        next_entry = PlaylistEntry.get_next()

        return self.player_play_song(next_entry, *args, **kwargs)

    def player_play_song(self, playlist_entry, timing=timedelta(),
                         paused=False, in_transition=False):
        """Set the player playing the provided song
        """
        # request the entry to play
        playlist_entry.set_playing()

        # set the player to an arbitrary state
        player = Player.get_or_create()
        player.update(
            timing=timing,
            paused=paused,
            in_transition=in_transition
        )
        player.save()

        return player

    def player_send_error(self, playlist_entry_id, message):
        """Simulate the player reporting an error
        """
        url = reverse('playlist-device-error')
        # Login as player
        self.authenticate(self.player)
        # Put as if playing next song
        response = self.client.post(
            url,
            {
                'playlist_entry': playlist_entry_id,
                'error_message': message,
            }
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class BaseAPITestCase(APITestCase, Provider):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # change logging level according to verbosity
        verbosity = self.get_verbosity()
        if verbosity <= 1:
            # disable all logging in quiet and normal mode
            logging.disable(logging.CRITICAL)

        elif verbosity == 2:
            # enable logging above DEBUG in verbose mode
            logging.disable(logging.DEBUG)

        # enable all logging in very verbose mode

    def get_verbosity(self):
        """Get the verbosity level

        Snippet from https://stackoverflow.com/a/27457315/4584444
        """
        for stack in reversed(inspect.stack()):
            options = stack[0].f_locals.get('options')
            if isinstance(options, dict):
                return int(options['verbosity'])

        return 1

    def tearDown(self):
        # Clear cache between tests, so that stored player state is re-init
        cache.clear()

    def authenticate(self, user):
        """Authenticate and set the token to the embedded client
        """
        token = super().authenticate(user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        return token

    def check_playlist_entry_json(self, json, expected_entry):
        """Method to check a representation against expected playlist entry
        """
        self.assertEqual(json['id'], expected_entry.id)
        self.assertEqual(json['owner']['id'], expected_entry.owner.id)
        self.assertEqual(json['song']['id'], expected_entry.song.id)

    def check_playlist_played_entry_json(self, json, expected_entry):
        """Method to check a representation against expected playlist played entry
        """
        self.check_playlist_entry_json(json, expected_entry)
        self.assertEqual(parse_datetime(json['date_played']),
                         expected_entry.date_played)
