from datetime import datetime
from unittest.mock import MagicMock, patch

from django.db.utils import OperationalError

from internal.tests.base_test import tz
from playlist.models import PlaylistEntry, Karaoke, clean_channel_names
from playlist.tests.base_test import PlaylistAPITestCase


class PlaylistEntryModelTestCase(PlaylistAPITestCase):
    """Test the playlist entry model
    """

    def setUp(self):
        self.create_test_data()

    def test_get_playing_success(self):
        """Test to get the currently playing entry
        """
        # pre assert no entry is playing
        self.assertIsNone(PlaylistEntry.get_playing())

        # set playlist entry 1 is playing
        self.pe1.date_played = datetime.now(tz)
        self.pe1.save()

        # assert playlist entry 1 is now playing
        self.assertEqual(PlaylistEntry.get_playing(), self.pe1)

        # set playlist entry 1 was played
        self.pe1.was_played = True
        self.pe1.save()

        # assert no entry is playing any more
        self.assertIsNone(PlaylistEntry.get_playing())

    def test_get_playing_abnormal(self):
        """Test to get the currently playing entry in abnormal condition
        """
        # pre assert no entry is playing
        self.assertIsNone(PlaylistEntry.get_playing())

        # set playlist entry 1 was played without setting it playing
        self.pe1.was_played = True
        self.pe1.save()

        # assert still no entry is playing
        self.assertIsNone(PlaylistEntry.get_playing())

        # set playlist entry 1 is playing after setting it played
        self.pe1.date_played = datetime.now(tz)
        self.pe1.save()

        # assert still no entry is playing
        self.assertIsNone(PlaylistEntry.get_playing())

    def test_get_playing_fail(self):
        """Test when several entries are supposed to play simultaneously
        """
        # pre assert no entry is playing
        self.assertIsNone(PlaylistEntry.get_playing())

        # set playlist entries 1 and 2 are playing
        self.pe1.date_played = datetime.now(tz)
        self.pe1.save()
        self.pe2.date_played = datetime.now(tz)
        self.pe2.save()

        # assert the method raises an exception
        with self.assertRaises(RuntimeError) as context_manager:
            PlaylistEntry.get_playing()

        # assert the error message contains the two playlist entries song
        self.assertIn(str(self.pe1.song), str(context_manager.exception))
        self.assertIn(str(self.pe2.song), str(context_manager.exception))

    def test_get_playlist_normal(self):
        """Test to get the playlist
        """
        # pre assert there are 2 entries in playlist
        playlist = PlaylistEntry.get_playlist()
        self.assertEqual(len(playlist), 2)
        self.assertEqual(playlist[0], self.pe1)
        self.assertEqual(playlist[1], self.pe2)

        # set playlist entry 1 is playing
        self.pe1.date_played = datetime.now(tz)
        self.pe1.save()

        # assert there is one entry in playlist
        playlist = PlaylistEntry.get_playlist()
        self.assertEqual(len(playlist), 1)
        self.assertEqual(playlist[0], self.pe2)

        # set playlist entry 1 was played
        self.pe1.was_played = True
        self.pe1.save()

        # assert there is still one entry in playlist
        playlist = PlaylistEntry.get_playlist()
        self.assertEqual(len(playlist), 1)
        self.assertEqual(playlist[0], self.pe2)

    def test_get_playlist_abnormal(self):
        """Test to get the playlist in abnormal condition
        """
        # pre assert there are 2 entries in playlist
        playlist = PlaylistEntry.get_playlist()
        self.assertEqual(len(playlist), 2)
        self.assertEqual(playlist[0], self.pe1)
        self.assertEqual(playlist[1], self.pe2)

        # set playlist entry 1 was played without setting it playing
        self.pe1.was_played = True
        self.pe1.save()

        # assert there is one entry in playlist
        playlist = PlaylistEntry.get_playlist()
        self.assertEqual(len(playlist), 1)
        self.assertEqual(playlist[0], self.pe2)

        # set playlist entry 1 is playing after setting it played
        self.pe1.date_played = datetime.now(tz)
        self.pe1.save()

        # assert there is still one entry in playlist
        playlist = PlaylistEntry.get_playlist()
        self.assertEqual(len(playlist), 1)
        self.assertEqual(playlist[0], self.pe2)

    def test_get_playlist_played_normal(self):
        """Test to get the playlist of played entries
        """
        # pre assert there are 2 entries played
        playlist_played = PlaylistEntry.get_playlist_played()
        self.assertEqual(len(playlist_played), 2)
        self.assertEqual(playlist_played[0], self.pe3)
        self.assertEqual(playlist_played[1], self.pe4)

        # set playlist entry 1 is playing
        self.pe1.date_played = datetime.now(tz)
        self.pe1.save()

        # assert there are still 2 entries played
        playlist_played = PlaylistEntry.get_playlist_played()
        self.assertEqual(len(playlist_played), 2)
        self.assertEqual(playlist_played[0], self.pe3)
        self.assertEqual(playlist_played[1], self.pe4)

        # set playlist entry 1 was played
        self.pe1.was_played = True
        self.pe1.save()

        # assert there are now 3 entries played
        playlist_played = PlaylistEntry.get_playlist_played()
        self.assertEqual(len(playlist_played), 3)
        self.assertEqual(playlist_played[0], self.pe1)
        self.assertEqual(playlist_played[1], self.pe3)
        self.assertEqual(playlist_played[2], self.pe4)

    def test_get_playlist_played_abnormal(self):
        """Test to get the playlist of played entries in abnormal condition
        """
        # pre assert there are 2 entries played
        playlist_played = PlaylistEntry.get_playlist_played()
        self.assertEqual(len(playlist_played), 2)
        self.assertEqual(playlist_played[0], self.pe3)
        self.assertEqual(playlist_played[1], self.pe4)

        # set playlist entry 1 was played without setting it playing
        self.pe1.was_played = True
        self.pe1.save()

        # assert there are now 3 entries played
        playlist_played = PlaylistEntry.get_playlist_played()
        self.assertEqual(len(playlist_played), 3)
        self.assertEqual(playlist_played[0], self.pe1)
        self.assertEqual(playlist_played[1], self.pe3)
        self.assertEqual(playlist_played[2], self.pe4)

        # set playlist entry 1 is playing after setting it played
        self.pe1.date_played = datetime.now(tz)
        self.pe1.save()

        # assert there are still 3 entries played
        playlist_played = PlaylistEntry.get_playlist_played()
        self.assertEqual(len(playlist_played), 3)
        self.assertEqual(playlist_played[0], self.pe1)
        self.assertEqual(playlist_played[1], self.pe3)
        self.assertEqual(playlist_played[2], self.pe4)

    def test_get_next_normal(self):
        """Test to get the next entry to play
        """
        # pre assert the next entry is playlist entry 1
        self.assertEqual(PlaylistEntry.get_next(), self.pe1)

        # set playlist entry 1 is playing
        self.pe1.date_played = datetime.now(tz)
        self.pe1.save()

        # assert the next entry is still playlist entry 1
        self.assertEqual(PlaylistEntry.get_next(), self.pe1)

        # set playlist entry 1 was played
        self.pe1.was_played = True
        self.pe1.save()

        # assert the next entry is now playlist entry 2
        self.assertEqual(PlaylistEntry.get_next(), self.pe2)

        # set playlist entry 2 played
        self.pe2.date_played = datetime.now(tz)
        self.pe2.was_played = True
        self.pe2.save()

        # assert there are no next entries now
        self.assertIsNone(PlaylistEntry.get_next())

    def test_get_next_abnormal(self):
        """Test to get the next entry to play in abnormal condition
        """
        # pre assert the next entry is playlist entry 1
        self.assertEqual(PlaylistEntry.get_next(), self.pe1)

        # set playlist entry 1 was played without setting it playing
        self.pe1.was_played = True
        self.pe1.save()

        # assert the next entry is now playlist entry 2
        self.assertEqual(PlaylistEntry.get_next(), self.pe2)

        # set playlist entry 1 is playing after setting it played
        self.pe1.date_played = datetime.now(tz)
        self.pe1.save()

        # assert the next entry is still playlist entry 2
        self.assertEqual(PlaylistEntry.get_next(), self.pe2)

    def test_get_next_relative(self):
        """Test to get the next entry from a specific one
        """
        # pre assert the entry after playlist entry 1 is playlist entry 2
        self.assertEqual(PlaylistEntry.get_next(self.pe1.id), self.pe2)

        # set playlist entry 1 is playing
        self.pe1.date_played = datetime.now(tz)
        self.pe1.save()

        # assert the entry after playlist entry 1 is still playlist entry 2
        self.assertEqual(PlaylistEntry.get_next(self.pe1.id), self.pe2)

        # set playlist entry 1 was played
        self.pe1.was_played = True
        self.pe1.save()

        # assert there are no entry after playlist entry 1 (since it was
        # played)
        self.assertIsNone(PlaylistEntry.get_next(self.pe1.id))

        # assert there are no entry after playlist entry 2 (since there are no
        # othe entries)
        self.assertIsNone(PlaylistEntry.get_next(self.pe2.id))


class KaraokeTestCase(PlaylistAPITestCase):
    """Test the Karaoke class
    """

    def setUp(self):
        self.create_test_data()

    def test_str_ongoing(self):
        """Test stringification
        """
        self.set_karaoke(ongoing=True)
        karaoke = Karaoke.get_object()
        self.assertEqual(str(karaoke), "Ongoing")

    def test_str_stopped(self):
        """Test stringification
        """
        self.set_karaoke(ongoing=False)
        karaoke = Karaoke.get_object()
        self.assertEqual(str(karaoke), "Stopped")

    @patch.object(Karaoke.objects, "all")
    def test_clean_channel_names(self, mocked_all):
        """Test to clean all channel names
        """
        karaoke1 = MagicMock()
        mocked_all.side_effect = [[karaoke1]]

        Karaoke.clean_channel_names()

        self.assertIsNone(karaoke1.channel_name)
        karaoke1.save.assert_called_with()


@patch.object(Karaoke, "clean_channel_names")
class CleanChannelNamesTestCase(PlaylistAPITestCase):
    """Test the clean_channel_names function
    """

    def test_clean_success(self, mocked_clean_channel_names):
        """Test to request to clean channel names successfuly
        """
        clean_channel_names()
        mocked_clean_channel_names.assert_called_with()

    def test_clean_failure(self, mocked_clean_channel_names):
        """Test to request to clean channels names unsuccessfuly
        """
        mocked_clean_channel_names.side_effect = OperationalError("error message")
        clean_channel_names()
