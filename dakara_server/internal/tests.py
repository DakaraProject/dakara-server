from django.conf import settings
from django.core.urlresolvers import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class VersionViewAPITestCase(APITestCase):
    url = reverse('version')

    def test_get_version(self):
        """Test to verify get version
        """
        # Get version
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['version'], settings.VERSION)
        self.assertEqual(response.data['date'], settings.DATE)
