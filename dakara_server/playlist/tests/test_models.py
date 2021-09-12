from datetime import datetime
from unittest.mock import MagicMock

import pytest
from django.db.utils import OperationalError

from internal.tests.base_test import tz
from playlist import models


@pytest.mark.django_db(transaction=True)
class TestPlaylistEntry:
    """Test the PlaylistEntry model."""

    def test_get_playing_success(self, playlist_provider):
        """Test to get the currently playing entry."""
        # pre assert no entry is playing
        assert models.PlaylistEntry.objects.get_playing() is None

        # set playlist entry 1 is playing
        playlist_provider.pe1.date_played = datetime.now(tz)
        playlist_provider.pe1.save()

        # assert playlist entry 1 is now playing
        assert models.PlaylistEntry.objects.get_playing() == playlist_provider.pe1

        # set playlist entry 1 was played
        playlist_provider.pe1.was_played = True
        playlist_provider.pe1.save()

        # assert no entry is playing any more
        assert models.PlaylistEntry.objects.get_playing() is None

    def test_get_playing_abnormal(self, playlist_provider):
        """Test to get the currently playing entry in abnormal condition."""
        # pre assert no entry is playing
        assert models.PlaylistEntry.objects.get_playing() is None

        # set playlist entry 1 was played without setting it playing
        playlist_provider.pe1.was_played = True
        playlist_provider.pe1.save()

        # assert still no entry is playing
        assert models.PlaylistEntry.objects.get_playing() is None

        # set playlist entry 1 is playing after setting it played
        playlist_provider.pe1.date_played = datetime.now(tz)
        playlist_provider.pe1.save()

        # assert still no entry is playing
        assert models.PlaylistEntry.objects.get_playing() is None

    def test_get_playing_fail(self, playlist_provider):
        """Test when several entries are supposed to play simultaneously."""
        # pre assert no entry is playing
        assert models.PlaylistEntry.objects.get_playing() is None

        # set playlist entries 1 and 2 are playing
        playlist_provider.pe1.date_played = datetime.now(tz)
        playlist_provider.pe1.save()
        playlist_provider.pe2.date_played = datetime.now(tz)
        playlist_provider.pe2.save()

        # assert the method raises an exception
        with pytest.raises(
            RuntimeError,
            match=r"{}.*{}".format(
                playlist_provider.pe1.song, playlist_provider.pe2.song
            ),
        ):
            models.PlaylistEntry.objects.get_playing()

    def test_get_playlist_normal(self, playlist_provider):
        """Test to get the playlist."""
        # pre assert there are 2 entries in playlist
        playlist = models.PlaylistEntry.objects.get_playlist()
        assert len(playlist) == 2
        assert playlist[0] == playlist_provider.pe1
        assert playlist[1] == playlist_provider.pe2

        # set playlist entry 1 is playing
        playlist_provider.pe1.date_played = datetime.now(tz)
        playlist_provider.pe1.save()

        # assert there is one entry in playlist
        playlist = models.PlaylistEntry.objects.get_playlist()
        assert len(playlist) == 1
        assert playlist[0] == playlist_provider.pe2

        # set playlist entry 1 was played
        playlist_provider.pe1.was_played = True
        playlist_provider.pe1.save()

        # assert there is still one entry in playlist
        playlist = models.PlaylistEntry.objects.get_playlist()
        assert len(playlist) == 1
        assert playlist[0] == playlist_provider.pe2

    def test_get_playlist_abnormal(self, playlist_provider):
        """Test to get the playlist in abnormal condition."""
        # pre assert there are 2 entries in playlist
        playlist = models.PlaylistEntry.objects.get_playlist()
        assert len(playlist) == 2
        assert playlist[0] == playlist_provider.pe1
        assert playlist[1] == playlist_provider.pe2

        # set playlist entry 1 was played without setting it playing
        playlist_provider.pe1.was_played = True
        playlist_provider.pe1.save()

        # assert there is one entry in playlist
        playlist = models.PlaylistEntry.objects.get_playlist()
        assert len(playlist) == 1
        assert playlist[0] == playlist_provider.pe2

        # set playlist entry 1 is playing after setting it played
        playlist_provider.pe1.date_played = datetime.now(tz)
        playlist_provider.pe1.save()

        # assert there is still one entry in playlist
        playlist = models.PlaylistEntry.objects.get_playlist()
        assert len(playlist) == 1
        assert playlist[0] == playlist_provider.pe2

    def test_get_playlist_played_normal(self, playlist_provider):
        """Test to get the playlist of played entries."""
        # pre assert there are 2 entries played
        playlist_played = models.PlaylistEntry.objects.get_playlist_played()
        assert len(playlist_played) == 2
        assert playlist_played[0] == playlist_provider.pe3
        assert playlist_played[1] == playlist_provider.pe4

        # set playlist entry 1 is playing
        playlist_provider.pe1.date_played = datetime.now(tz)
        playlist_provider.pe1.save()

        # assert there are still 2 entries played
        playlist_played = models.PlaylistEntry.objects.get_playlist_played()
        assert len(playlist_played) == 2
        assert playlist_played[0] == playlist_provider.pe3
        assert playlist_played[1] == playlist_provider.pe4

        # set playlist entry 1 was played
        playlist_provider.pe1.was_played = True
        playlist_provider.pe1.save()

        # assert there are now 3 entries played
        playlist_played = models.PlaylistEntry.objects.get_playlist_played()
        assert len(playlist_played) == 3
        assert playlist_played[0] == playlist_provider.pe1
        assert playlist_played[1] == playlist_provider.pe3
        assert playlist_played[2] == playlist_provider.pe4

    def test_get_playlist_played_abnormal(self, playlist_provider):
        """Test to get the playlist of played entries in abnormal condition."""
        # pre assert there are 2 entries played
        playlist_played = models.PlaylistEntry.objects.get_playlist_played()
        assert len(playlist_played) == 2
        assert playlist_played[0] == playlist_provider.pe3
        assert playlist_played[1] == playlist_provider.pe4

        # set playlist entry 1 was played without setting it playing
        playlist_provider.pe1.was_played = True
        playlist_provider.pe1.save()

        # assert there are now 3 entries played
        playlist_played = models.PlaylistEntry.objects.get_playlist_played()
        assert len(playlist_played) == 3
        assert playlist_played[0] == playlist_provider.pe1
        assert playlist_played[1] == playlist_provider.pe3
        assert playlist_played[2] == playlist_provider.pe4

        # set playlist entry 1 is playing after setting it played
        playlist_provider.pe1.date_played = datetime.now(tz)
        playlist_provider.pe1.save()

        # assert there are still 3 entries played
        playlist_played = models.PlaylistEntry.objects.get_playlist_played()
        assert len(playlist_played) == 3
        assert playlist_played[0] == playlist_provider.pe1
        assert playlist_played[1] == playlist_provider.pe3
        assert playlist_played[2] == playlist_provider.pe4

    def test_get_next_normal(self, playlist_provider):
        """Test to get the next entry to play."""
        # pre assert the next entry is playlist entry 1
        assert models.PlaylistEntry.objects.get_next() == playlist_provider.pe1

        # set playlist entry 1 is playing
        playlist_provider.pe1.date_played = datetime.now(tz)
        playlist_provider.pe1.save()

        # assert the next entry is still playlist entry 1
        assert models.PlaylistEntry.objects.get_next() == playlist_provider.pe1

        # set playlist entry 1 was played
        playlist_provider.pe1.was_played = True
        playlist_provider.pe1.save()

        # assert the next entry is now playlist entry 2
        assert models.PlaylistEntry.objects.get_next() == playlist_provider.pe2

        # set playlist entry 2 played
        playlist_provider.pe2.date_played = datetime.now(tz)
        playlist_provider.pe2.was_played = True
        playlist_provider.pe2.save()

        # assert there are no next entries now
        assert models.PlaylistEntry.objects.get_next() is None

    def test_get_next_abnormal(self, playlist_provider):
        """Test to get the next entry to play in abnormal condition."""
        # pre assert the next entry is playlist entry 1
        assert models.PlaylistEntry.objects.get_next() == playlist_provider.pe1

        # set playlist entry 1 was played without setting it playing
        playlist_provider.pe1.was_played = True
        playlist_provider.pe1.save()

        # assert the next entry is now playlist entry 2
        assert models.PlaylistEntry.objects.get_next() == playlist_provider.pe2

        # set playlist entry 1 is playing after setting it played
        playlist_provider.pe1.date_played = datetime.now(tz)
        playlist_provider.pe1.save()

        # assert the next entry is still playlist entry 2
        assert models.PlaylistEntry.objects.get_next() == playlist_provider.pe2

    def test_get_next_relative(self, playlist_provider):
        """Test to get the next entry from a specific one."""
        # pre assert the entry after playlist entry 1 is playlist entry 2
        assert (
            models.PlaylistEntry.objects.get_next(playlist_provider.pe1.id)
            == playlist_provider.pe2
        )

        # set playlist entry 1 is playing
        playlist_provider.pe1.date_played = datetime.now(tz)
        playlist_provider.pe1.save()

        # assert the entry after playlist entry 1 is still playlist entry 2
        assert (
            models.PlaylistEntry.objects.get_next(playlist_provider.pe1.id)
            == playlist_provider.pe2
        )

        # set playlist entry 1 was played
        playlist_provider.pe1.was_played = True
        playlist_provider.pe1.save()

        # assert there are no entry after playlist entry 1 (since it was
        # played)
        assert models.PlaylistEntry.objects.get_next(playlist_provider.pe1.id) is None

        # assert there are no entry after playlist entry 2 (since there are no
        # othe entries)
        assert models.PlaylistEntry.objects.get_next(playlist_provider.pe2.id) is None

    def test_set_playing(self, playlist_provider):
        """Test to set a playlist entry playing."""
        # pre assert no entry is playing
        assert models.PlaylistEntry.objects.get_playing() is None

        # play next playlist entry
        playlist_entry = models.PlaylistEntry.objects.get_next()
        playlist_entry.set_playing()

        # assert entry is playing
        assert models.PlaylistEntry.objects.get_playing() == playlist_entry

    def test_set_playing_already_playing(self, playlist_provider):
        """Test to set a playlist entry playing when one is already playing."""
        # play next playlist entry
        playlist_entry_current = models.PlaylistEntry.objects.get_next()
        playlist_entry_current.set_playing()
        playlist_entry_next = models.PlaylistEntry.objects.get_next(
            playlist_entry_current.id
        )

        # assert you cannot play another entry
        with pytest.raises(RuntimeError, match="A playlist entry is currently in play"):
            playlist_entry_next.set_playing()

    def test_set_finished(self, playlist_provider):
        """Test to finish a playlist entry."""
        playlist_entry_current = models.PlaylistEntry.objects.get_next()

        # pre assert current playlist entry is not played
        assert not playlist_entry_current.was_played

        # play and finish the song
        playlist_entry_current.set_playing()
        playlist_entry_current.set_finished()

        # assert current playlist entry was played
        assert playlist_entry_current.was_played

    def test_set_finished_not_playing(self, playlist_provider):
        """Test to finish a playlist entry when it was not playing."""
        playlist_entry_current = models.PlaylistEntry.objects.get_next()

        # pre assert current playlist entry is not played
        assert not playlist_entry_current.was_played

        # pre assert you cannot finish unplaying current playlist
        with pytest.raises(RuntimeError, match="This playlist entry is not playing"):
            playlist_entry_current.set_finished()


class TestKaraoke:
    """Test the Karaoke class."""

    def test_clean_channel_names(self, mocker):
        """Test to clean all channel names."""
        mocked_all = mocker.patch.object(models.Karaoke.objects, "all")
        karaoke1 = MagicMock()
        mocked_all.side_effect = [[karaoke1]]

        models.Karaoke.objects.clean_channel_names()

        assert karaoke1.channel_name is None
        karaoke1.save.assert_called_with()


class TestCleanChannel:
    """Test the clean_channel_names function."""

    def test_clean_success(self, mocker):
        """Test to request to clean channel names successfuly."""
        mocked_clean_channel_names = mocker.patch.object(
            models.Karaoke.objects, "clean_channel_names"
        )
        models.clean_channel_names()
        mocked_clean_channel_names.assert_called_with()

    def test_clean_failure(self, mocker):
        """Test to request to clean channels names unsuccessfuly."""
        mocked_clean_channel_names = mocker.patch.object(
            models.Karaoke.objects, "clean_channel_names"
        )
        mocked_clean_channel_names.side_effect = OperationalError("error message")
        models.clean_channel_names()


class TestStringification:
    """Test the string methods."""

    @pytest.mark.django_db(transaction=True)
    def test_playlist_entry_str(self, playlist_provider):
        """Test the string representation of a playlist entry."""
        playlist_entry = models.PlaylistEntry(
            song=playlist_provider.song1, owner=playlist_provider.user
        )

        assert str(playlist_entry) == "Song1 (for TestUser)"

    def test_karaoke_str(self):
        """Test the string representation of a karaoke object."""
        karaoke = models.Karaoke(date_stop=datetime(year=1970, month=1, day=1))

        assert str(karaoke) == "karaoke None"

    @pytest.mark.django_db(transaction=True)
    def test_player_error_str(self, playlist_provider):
        """Test the string representation of a player error."""
        player_error1 = models.PlayerError(
            playlist_entry=playlist_provider.pe1, error_message="Error message"
        )

        assert str(player_error1) == "Song1 (for testPlaylistManager): Error message"

        player_error2 = models.PlayerError(
            playlist_entry=playlist_provider.pe1,
            error_message="Very long error message with a lot of details that you do "
            "not want to display",
        )

        assert (
            str(player_error2)
            == "Song1 (for testPlaylistManager): Very long error message with a "
            "lot of [...]"
        )

    def test_player_str(self):
        """Test the string representation of a player."""
        player = models.Player()

        assert str(player) == "player None"
