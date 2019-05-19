from datetime import timedelta

from django.core.urlresolvers import reverse
from django.contrib.auth import get_user_model
from rest_framework import status

from library.base_test import BaseAPITestCase
from library.models import Song, SongWorkLink


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
                {"filename": self.song1.filename, "directory": self.song1.directory},
                {"filename": self.song2.filename, "directory": self.song2.directory},
            ],
        )

    def test_get_song_list_forbidden(self):
        """Test that normal user cannot have feeder song list
        """
        # Login as simple user
        self.authenticate(self.user)

        # Attempte to get songs list
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class FeederViewTestCase(BaseAPITestCase):
    url = reverse("library-feeder")

    def setUp(self):
        # create a user without any rights
        self.user = self.create_user("TestUser")

        # create a manager
        self.manager = self.create_user("TestManager", library_level=UserModel.MANAGER)

        # create test data
        self.create_library_test_data()

    def test_add(self):
        # Login as manager
        self.authenticate(self.manager)

        # pre assert the amount of songs
        self.assertEqual(Song.objects.count(), 2)

        # create song
        song = {
            "title": "Song new",
            "filename": "song new",
            "directory": "directory new",
            "duration": timedelta(seconds=1),
            "artists": [{"name": self.artist1.name}],
            "tags": [{"name": self.tag1.name}],
            "works": [
                {
                    "work": {
                        "title": self.work1.title,
                        "subtitle": self.work1.subtitle,
                        "work_type": {"query_name": self.work1.work_type.query_name},
                    },
                    "link_type": "OP",
                    "link_type_number": None,
                    "episodes": "",
                }
            ],
        }
        response = self.client.post(self.url, {"added": [song], "deleted": []})

        # assert the response
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # assert the created song
        self.assertEqual(Song.objects.count(), 3)
        song = Song.objects.get(filename="song new", directory="directory new")
        self.assertEqual(song.title, "Song new")
        self.assertEqual(song.duration, timedelta(seconds=1))
        self.assertCountEqual(song.artists.all(), [self.artist1])
        self.assertCountEqual(song.tags.all(), [self.tag1])
        self.assertEqual(song.songworklink_set.all().count(), 1)
        song_work_link_1 = SongWorkLink.objects.get(song=song, work=self.work1)
        self.assertCountEqual(song.songworklink_set.all(), [song_work_link_1])

    def test_delete(self):
        # Login as manager
        self.authenticate(self.manager)

        # pre assert the amount of songs
        self.assertEqual(Song.objects.count(), 2)

        response = self.client.post(
            self.url,
            {
                "added": [],
                "deleted": [
                    {"filename": self.song1.filename, "directory": self.song1.directory}
                ],
            },
        )

        # assert the response
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # assert the deleted song
        self.assertEqual(Song.objects.count(), 1)
        self.assertEqual(
            Song.objects.filter(
                filename=self.song1.filename, directory=self.song1.directory
            ).count(),
            0,
        )
