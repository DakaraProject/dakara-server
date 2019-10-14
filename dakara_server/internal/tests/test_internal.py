from unittest.mock import patch

from django.core.urlresolvers import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from internal.version import check_version


class VersionViewAPITestCase(APITestCase):
    url = reverse("version")

    def test_get_version(self):
        """Test to verify get version
        """
        # get version
        with self.settings(VERSION="0.0.0", DATE="1970-01-01"):
            response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # check the version matches
        self.assertEqual(response.data["version"], "0.0.0")
        self.assertEqual(response.data["date"], "1970-01-01")


@patch("internal.version.logger")
class CheckVersionTestCase(APITestCase):
    def test_check_release(self, mocked_logger):
        """Test the version check for a release
        """
        # check the version
        with self.settings(VERSION="0.0.0", DATE="1970-01-01"):
            check_version()

        # assert the logs
        # NOTE I don't like the way I assert the logs. Normally, I should use
        # `with self.assertLogs() as logger` and make tests on `logger`. This
        # is the clean way to assert logs in Python. This unfortunately doesn't
        # work when executing the whole test suite, as I think Django does some
        # magic when initializing the loggers.
        mocked_logger.info.assert_called_with("Dakara server 0.0.0 (1970-01-01)")

    def test_check_non_release(self, mocked_logger):
        """Test the version check for a non release
        """
        # check the version
        with self.settings(VERSION="0.0.0-dev", DATE="1970-01-01"):
            check_version()

        # assert the logs
        # NOTE see above note.
        mocked_logger.info.assert_called_with("Dakara server 0.0.0-dev (1970-01-01)")
        mocked_logger.warning.assert_called_with(
            "You are running a dev version, use it at your own risks!"
        )
