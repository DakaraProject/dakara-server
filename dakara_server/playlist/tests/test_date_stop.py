from datetime import datetime, timedelta
from unittest.mock import patch

from django.db.utils import OperationalError

from playlist.date_stop import clear_date_stop, check_date_stop_on_app_ready
from playlist.models import Karaoke
from playlist.tests.base_test import BaseAPITestCase, tz


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


class CheckDateStopOnAppReadyTestCase(BaseAPITestCase):
    @patch("playlist.date_stop.clear_date_stop")
    @patch("playlist.date_stop.scheduler")
    def test_check_date_expired(self, mocked_scheduler, mocked_clear_date_stop):
        """Check clear date stop is called when date has expired
        """

        # Set stop date in the past
        karaoke = Karaoke.get_object()
        karaoke.date_stop = datetime.now(tz) - timedelta(minutes=10)
        karaoke.save()

        # Call method
        check_date_stop_on_app_ready()

        # Check clear date stop was called
        mocked_clear_date_stop.assert_called_with()

        # Check add job was not called
        mocked_scheduler.add_job.assert_not_called()

    @patch("playlist.date_stop.clear_date_stop")
    @patch("playlist.date_stop.scheduler")
    def test_date_not_expired(self, mocked_scheduler, mocked_clear_date_stop):
        """Check job is scheduled when date not expired
        """
        # Mock return value of add_job
        mocked_scheduler.add_job.return_value.id = "job_id"

        # Set stop date in the future
        karaoke = Karaoke.get_object()
        date_stop = datetime.now(tz) + timedelta(minutes=10)
        karaoke.date_stop = date_stop
        karaoke.save()

        # Call method
        check_date_stop_on_app_ready()

        # Check clear date stop was not called
        mocked_clear_date_stop.assert_not_called()

        # Check add job was called
        mocked_scheduler.add_job.assert_called_with(
            mocked_clear_date_stop, "date", run_date=date_stop
        )

    @patch("playlist.date_stop.clear_date_stop")
    @patch("playlist.date_stop.scheduler")
    def test_no_date(self, mocked_scheduler, mocked_clear_date_stop):
        """Check nothing happen when date stop is not set
        """
        # Assert stop date is not set
        karaoke = Karaoke.get_object()
        self.assertIsNone(karaoke.date_stop)

        # Call method
        check_date_stop_on_app_ready()

        # Check clear date stop was not called
        mocked_clear_date_stop.assert_not_called()

        # Check add job was not called
        mocked_scheduler.add_job.assert_not_called()

    @patch("playlist.date_stop.scheduler")
    def test_date_not_expired_called_twice(self, mocked_scheduler):
        """Check job is scheduled only once when date not expired
        """
        # Mock return value of add_job
        mocked_scheduler.add_job.return_value.id = "job_id"

        # Set stop date in the future
        karaoke = Karaoke.get_object()
        date_stop = datetime.now(tz) + timedelta(minutes=10)
        karaoke.date_stop = date_stop
        karaoke.save()

        # Call method
        check_date_stop_on_app_ready()

        # Check add job was called
        mocked_scheduler.add_job.assert_called_with(
            clear_date_stop, "date", run_date=date_stop
        )

        mocked_scheduler.reset_mock()

        # Call method a second time
        check_date_stop_on_app_ready()

        # Check add job was not called
        mocked_scheduler.add_job.assert_not_called()

    @patch("playlist.date_stop.Karaoke")
    @patch("playlist.date_stop.clear_date_stop")
    @patch("playlist.date_stop.scheduler")
    def test_database_unavailable(
        self, mocked_scheduler, mocked_clear_date_stop, MockedKaraoke
    ):
        """Check there is no crash if the database does not exist

        We simulate a crash by raising a `django.db.utils.OperationalError`
        when accessing to `Karaoke.get_object`.
        """
        # mock the karaoke mock to crash when invoking class method get_object
        MockedKaraoke.get_object.side_effect = OperationalError(
            "no such table: playlist_karaoke"
        )

        # call the method
        check_date_stop_on_app_ready()

        # check clear date stop was not called
        mocked_clear_date_stop.assert_not_called()

        # check add job was not called
        mocked_scheduler.add_job.assert_not_called()
