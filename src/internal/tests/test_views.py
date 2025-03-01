from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class SettingsViewTestCase(APITestCase):
    url = reverse("settings")

    def test_get_settings(self):
        """Test to verify get project settings."""
        # get settings
        with self.settings(VERSION="0.0.0", DATE="1970-01-01", EMAIL_ENABLED=True):
            response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # check the settings matches
        self.assertEqual(response.data["version"], "0.0.0")
        self.assertEqual(response.data["date"], "1970-01-01")
        self.assertTrue(response.data["email_enabled"])
