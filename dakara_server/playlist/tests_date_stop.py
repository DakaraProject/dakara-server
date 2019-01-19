from datetime import datetime, timedelta
from unittest.mock import patch

from .base_test import BaseAPITestCase, tz

from playlist.date_stop import clear_date_stop
from playlist.models import Karaoke


class ClearDateStopTestCase(BaseAPITestCase):
    @patch("playlist.date_stop.logger")
    def test_date_stop_cleared(self, mocked_logger):
        """Check karaoke was modified when date stop has expired
        """

        # Set up karaoke with date stop and can add to playlist enabled
        karaoke = Karaoke.get_object()
        self.assertTrue(karaoke.can_add_to_playlist)
        karaoke.date_stop = datetime.now(tz) - timedelta(minutes=10)
        karaoke.save()

        clear_date_stop()

        # Check clear date stop was cleared and can add to playlist was disabled
        karaoke = Karaoke.get_object()
        self.assertFalse(karaoke.can_add_to_playlist)
        self.assertIsNone(karaoke.date_stop)

        # Check logger was not called
        mocked_logger.error.assert_not_called()

    @patch("playlist.date_stop.logger")
    def test_date_stop_not_cleared(self, mocked_logger):
        """Check karaoke was not modified when date stop has not expired
        """

        # Set up karaoke with date stop and can add to playlist enabled
        karaoke = Karaoke.get_object()
        self.assertTrue(karaoke.can_add_to_playlist)
        karaoke.date_stop = datetime.now(tz) + timedelta(minutes=10)
        karaoke.save()

        clear_date_stop()

        # Check clear date stop was cleared and can add to playlist was disabled
        karaoke_new = Karaoke.get_object()
        self.assertTrue(karaoke_new.can_add_to_playlist)
        self.assertEqual(karaoke_new.date_stop, karaoke.date_stop)

        # Check logger was called
        mocked_logger.error.assert_called_with(
            "Clear date stop was called when it should not"
        )
