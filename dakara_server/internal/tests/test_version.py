from django.test import TestCase

from internal.version import check_version


class CheckVersionTestCase(TestCase):
    def test_check_release(self):
        """Test the version check for a release."""
        # check the version
        with self.assertLogs("django", "DEBUG") as logger:
            with self.settings(VERSION="0.0.0", DATE="1970-01-01"):
                check_version()

        # assert the logs
        self.assertListEqual(
            logger.output, ["INFO:django:Dakara server 0.0.0 (1970-01-01)"]
        )

    def test_check_non_release(self):
        """Test the version check for a non release."""
        # check the version
        with self.assertLogs("django", "DEBUG") as logger:
            with self.settings(VERSION="0.0.0-dev", DATE="1970-01-01"):
                check_version()

        # assert the logs
        self.assertListEqual(
            logger.output,
            [
                "INFO:django:Dakara server 0.0.0-dev (1970-01-01)",
                "WARNING:django:You are running a dev version, use it at your own "
                "risks!",
            ],
        )
