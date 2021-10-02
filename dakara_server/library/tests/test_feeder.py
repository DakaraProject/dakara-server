from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status

from library.tests.base_test import LibraryAPITestCase

UserModel = get_user_model()


class SongFeederListViewTestCase(LibraryAPITestCase):
    url = reverse("library-song-retrieve-list")

    def setUp(self):
        # create a user without any rights
        self.user = self.create_user("TestUser")

        # create a manager
        self.manager = self.create_user("TestManager", library_level=UserModel.MANAGER)

        # create test data
        self.create_test_data()

    def test_get_feeder_song_list(self):
        """Test to get feeder song list for manager."""
        # Login as manager
        self.authenticate(self.manager)

        # Get songs list
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

        # Songs are not sorted
        self.assertCountEqual(
            response.data,
            [
                {
                    "id": self.song1.pk,
                    "filename": self.song1.filename,
                    "directory": self.song1.directory,
                },
                {
                    "id": self.song2.pk,
                    "filename": self.song2.filename,
                    "directory": self.song2.directory,
                },
            ],
        )

    def test_get_song_list_forbidden(self):
        """Test that normal user cannot have feeder song list."""
        # Login as simple user
        self.authenticate(self.user)

        # Attempte to get songs list
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class WorkFeederListViewTestCase(LibraryAPITestCase):
    url = reverse("library-work-retrieve-list")

    def setUp(self):
        # create a user without any rights
        self.user = self.create_user("TestUser")

        # create a manager
        self.manager = self.create_user("TestManager", library_level=UserModel.MANAGER)

        # create test data
        self.create_test_data()

    def test_get_feeder_work_list(self):
        """Test to get feeder work list for manager."""
        # Login as manager
        self.authenticate(self.manager)

        # Get works list
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

        # Songs are not sorted
        self.maxDiff = None
        self.assertCountEqual(
            response.data,
            [
                {
                    "id": self.work1.pk,
                    "title": self.work1.title,
                    "subtitle": "",
                    "work_type": {"query_name": self.wt1.query_name},
                },
                {
                    "id": self.work2.pk,
                    "title": self.work2.title,
                    "subtitle": "",
                    "work_type": {"query_name": self.wt1.query_name},
                },
                {
                    "id": self.work3.pk,
                    "title": self.work3.title,
                    "subtitle": "",
                    "work_type": {"query_name": self.wt2.query_name},
                },
            ],
        )

    def test_get_work_list_forbidden(self):
        """Test that normal user cannot have feeder work list."""
        # Login as simple user
        self.authenticate(self.user)

        # Attempte to get songs list
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
