from datetime import datetime, timedelta

from internal.tests.base_test import tz
from playlist.date_stop import clear_date_stop
from playlist.models import Karaoke
from playlist.tests.base_test import PlaylistAPITestCase


class ClearDateStopTestCase(PlaylistAPITestCase):
    def test_date_stop_cleared(self):
        """Check karaoke was modified when date stop has expired."""

        # Set up karaoke with date stop and can add to playlist enabled
        karaoke = Karaoke.objects.get_object()
        self.assertTrue(karaoke.can_add_to_playlist)
        karaoke.date_stop = datetime.now(tz) - timedelta(minutes=10)
        karaoke.save()

        with self.assertLogs("playlist.date_stop", "DEBUG") as logger:
            clear_date_stop()

        # Check clear date stop was cleared and can add to playlist was disabled
        karaoke = Karaoke.objects.get_object()
        self.assertFalse(karaoke.can_add_to_playlist)
        self.assertIsNone(karaoke.date_stop)

        # Check logger
        self.assertListEqual(
            logger.output,
            [
                "INFO:playlist.date_stop:Date stop was cleared and can add to playlist "
                "was disabled"
            ],
        )

    def test_date_stop_not_cleared(self):
        """Check karaoke was not modified when date stop has not expired."""

        # Set up karaoke with date stop and can add to playlist enabled
        karaoke = Karaoke.objects.get_object()
        self.assertTrue(karaoke.can_add_to_playlist)
        karaoke.date_stop = datetime.now(tz) + timedelta(minutes=10)
        karaoke.save()

        clear_date_stop()

        # Check clear date stop was cleared and can add to playlist was disabled
        karaoke_new = Karaoke.objects.get_object()
        self.assertTrue(karaoke_new.can_add_to_playlist)
        self.assertEqual(karaoke_new.date_stop, karaoke.date_stop)
