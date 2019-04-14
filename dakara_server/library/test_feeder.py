from django.core.urlresolvers import reverse
from django.contrib.auth import get_user_model
from rest_framework import status

from .base_test import BaseAPITestCase


UserModel = get_user_model()


class FeederListViewTestCase(BaseAPITestCase):
    url = reverse("library-feeder-list")

    def setUp(self):
        # create a user without any rights
        self.user = self.create_user("TestUser")

        # create a manager
        self.manager = self.create_user("TestManager", library_level=UserModel.MANAGER)

        # create test data
        self.create_library_test_data()

    def test_get_feeder_song_list(self):
        """Test to get feeder song list for manager
        """
        # Login as simple user
        self.authenticate(self.manager)

        # Get songs list
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

        # Songs are sorted by title
        self.assertDictEqual(
            response.data[0],
            {"filename": self.song1.filename, "directory": self.song1.directory},
        )
        self.assertDictEqual(
            response.data[1],
            {"filename": self.song2.filename, "directory": self.song2.directory},
        )

    def test_get_song_list_forbidden(self):
        """Test that normal user cannot have feeder song list
        """
        # Login as simple user
        self.authenticate(self.user)

        # Attempte to get songs list
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
