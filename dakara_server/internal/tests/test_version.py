from django.urls import reverse
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


class CheckVersionTestCase(APITestCase):
    def test_check_release(self):
        """Test the version check for a release
        """
        # check the version
        with self.assertLogs("django", "DEBUG") as logger:
            with self.settings(VERSION="0.0.0", DATE="1970-01-01"):
                check_version()

        # assert the logs
        self.assertListEqual(
            logger.output, ["INFO:django:Dakara server 0.0.0 (1970-01-01)"]
        )

    def test_check_non_release(self):
        """Test the version check for a non release
        """
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
