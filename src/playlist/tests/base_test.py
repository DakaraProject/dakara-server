from datetime import datetime, timedelta

from django.core.cache import cache
from django.utils.dateparse import parse_datetime

from internal.tests.base_test import BaseAPITestCase, BaseProvider, UserModel, tz
from library.models import Song, SongTag
from playlist.models import Karaoke, Player, PlayerToken, PlaylistEntry


class PlaylistProvider(BaseProvider):
    """Provides helper functions for playlist tests."""

    def create_test_data(self):
        """Create test users songs, and playlist entries."""
        # create an admin
        self.admin = self.create_user("Admin", is_superuser=True)

        # create a user without any rights
        self.user = self.create_user("TestUser")

        # create a playlist user
        self.p_user = self.create_user(
            "TestPlaylistUser", playlist_level=UserModel.USER
        )

        # create a playlist manager
        self.manager = self.create_user(
            "testPlaylistManager", playlist_level=UserModel.MANAGER
        )

        # Create tags
        self.tag1 = SongTag(name="TAG1")
        self.tag1.save()

        # Create songs
        self.song1 = Song(title="Song1", duration=timedelta(seconds=5))
        self.song1.save()
        self.song1.tags.add(self.tag1)
        self.song2 = Song(
            title="Song2", duration=timedelta(seconds=10), has_instrumental=True
        )
        self.song2.save()

        # Create playlist entries
        self.pe1 = PlaylistEntry(song=self.song1, owner=self.manager)
        self.pe1.save()

        self.pe2 = PlaylistEntry(
            song=self.song2, owner=self.p_user, use_instrumental=True
        )
        self.pe2.save()

        self.pe3 = PlaylistEntry(
            song=self.song2,
            owner=self.manager,
            was_played=True,
            date_play=datetime.now(tz),
        )
        self.pe3.save()

        self.pe4 = PlaylistEntry(
            song=self.song1,
            owner=self.user,
            was_played=True,
            date_play=datetime.now(tz) - timedelta(minutes=15),
        )
        self.pe4.save()

    def set_karaoke(
        self, ongoing=None, can_add_to_playlist=None, player_play_next_song=None
    ):
        """Put the karaoke in stop state."""
        self.karaoke = Karaoke.objects.get_object()
        if ongoing is not None:
            self.karaoke.ongoing = ongoing

        if can_add_to_playlist is not None:
            self.karaoke.can_add_to_playlist = can_add_to_playlist

        if player_play_next_song is not None:
            self.karaoke.player_play_next_song = player_play_next_song

        self.karaoke.save()

    def player_play_next_song(self, *args, **kwargs):
        """Set the player playing the next song."""
        # get current entry
        current_entry = PlaylistEntry.objects.get_playing()

        if current_entry is not None:
            # set current entry as played
            current_entry.set_finished()

        # get next entry
        next_entry = PlaylistEntry.objects.get_next()

        return self.player_play_song(next_entry, *args, **kwargs)

    def player_play_song(
        self, playlist_entry, timing=timedelta(), paused=False, in_transition=False
    ):
        """Set the player playing the provided song."""
        # request the entry to play
        playlist_entry.set_playing()

        # set the player to an arbitrary state
        karaoke = Karaoke.objects.get_object()
        player, _ = Player.cache.get_or_create(karaoke=karaoke)
        player.timing = timing
        player.paused = paused
        player.in_transition = in_transition
        player.save()

        return player

    def check_playlist_entry_json(self, json, expected_entry):
        """Method to check a representation against expected playlist entry."""
        self.assertEqual(json["id"], expected_entry.id)
        self.assertEqual(json["owner"]["id"], expected_entry.owner.id)
        self.assertEqual(json["song"]["id"], expected_entry.song.id)
        self.assertEqual(json["use_instrumental"], expected_entry.use_instrumental)

    def check_playlist_played_entry_json(self, json, expected_entry):
        """Method to check a representation against expected playlist played entry."""
        self.check_playlist_entry_json(json, expected_entry)
        self.assertEqual(parse_datetime(json["date_play"]), expected_entry.date_play)

    def get_player_token(self):
        """Create and give player token."""
        karaoke = Karaoke.objects.get_object()
        return PlayerToken.objects.create(karaoke=karaoke).key


class PlaylistAPITestCase(BaseAPITestCase, PlaylistProvider):
    """Base playlist test class for Unittest."""

    def tearDown(self):
        # Clear cache between tests, so that stored player state is re-init
        cache.clear()
