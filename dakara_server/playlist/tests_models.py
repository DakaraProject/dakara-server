from datetime import datetime

from .base_test import BaseAPITestCase, tz

from .models import PlaylistEntry


class PlaylistEntryModelTestCase(BaseAPITestCase):
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
