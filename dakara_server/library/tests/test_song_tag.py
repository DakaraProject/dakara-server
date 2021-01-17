from django.urls import reverse
from rest_framework import status

from internal.tests.base_test import UserModel
from library.tests.base_test import LibraryAPITestCase
from library.models import SongTag


class SongTagListViewTestCase(LibraryAPITestCase):
    url = reverse("library-songtag-list")

    def setUp(self):
        # create a manager
        self.manager = self.create_user(
            "TestUserManager", library_level=UserModel.MANAGER
        )

        # create a user without any rights
        self.user = self.create_user("TestUser")

        # create test data
        self.create_test_data()

    def test_get_tag_list(self):
        """Test to verify tag list
        """
        # Login as simple user
        self.authenticate(self.user)

        # Get tags list
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)
        self.assertEqual(len(response.data["results"]), 2)

        # Tags are sorted by name
        self.check_tag_json(response.data["results"][0], self.tag1)
        self.check_tag_json(response.data["results"][1], self.tag2)

    def test_get_tag_list_forbidden(self):
        """Test to verify unauthenticated user can't get tag list
        """
        # Attempt to get work type list
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_post_tag_already_exists(self):
        """Test to create a tag when it already exists
        """
        # Login as simple user
        self.authenticate(self.manager)

        # create an existing tag
        response = self.client.post(self.url, {"name": "TAG1"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class SongTagViewTestCase(LibraryAPITestCase):
    def setUp(self):
        # create a manager
        self.manager = self.create_user(
            "TestUserManager", library_level=UserModel.MANAGER
        )

        self.user = self.create_user("TestUser")

        # create test data
        self.create_test_data()

        # create urls
        self.url_sg1 = reverse("library-songtag", kwargs={"pk": self.tag1.id})
        self.url_sg2 = reverse("library-songtag", kwargs={"pk": self.tag2.id})

    def test_update_song_tag_manager(self):
        """Test manager can update tag
        """
        # login as manager
        self.authenticate(self.manager)

        # pre-assertion: the tag is enabled
        tag = SongTag.objects.get(id=self.tag1.id)
        self.assertFalse(tag.disabled)

        # alter one tag
        response = self.client.patch(self.url_sg1, {"disabled": True})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # the tag should be disabled now
        tag = SongTag.objects.get(id=self.tag1.id)
        self.assertTrue(tag.disabled)

    def test_update_song_tag_user(self):
        """Test simple user can not update tags
        """
        # login as user
        self.authenticate(self.user)

        # attempt to alter one tag
        response = self.client.patch(self.url_sg1, {"disabled": True})

        # user can't update tag
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
