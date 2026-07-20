from django.urls import reverse
from rest_framework import status

from library.models import Artist
from library.tests.base_test import LibraryAPITestCase


class ArtistListViewTestCase(LibraryAPITestCase):
    url = reverse("library-artist-list")

    def setUp(self):
        # create a user without any rights
        self.user = self.create_user("TestUser")

        # create test data
        self.create_test_data()

    def test_get_artist_list(self):
        """Test to verify artist list with no query."""
        # Login as simple user
        self.authenticate(self.user)

        # Get artists list
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)
        self.assertEqual(len(response.data["results"]), 2)

        # Artists are sorted by name
        self.check_artist_json(response.data["results"][0], self.artist1)
        self.check_artist_json(response.data["results"][1], self.artist2)

        # Check song count
        self.assertEqual(response.data["results"][0]["song_count"], 1)
        self.assertEqual(response.data["results"][1]["song_count"], 0)

    def test_get_artist_list_forbidden(self):
        """Test to verify unauthenticated user can't get artist list."""
        # Attempt to get artists list
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_artist_list_with_query(self):
        """Test to verify artist list with query."""
        # Login as simple user
        self.authenticate(self.user)

        # Get artists list with query = "tist1"
        # Should only return artist1
        self.check_query("tist1", [self.artist1])

        # Get artists list with query = "ork1"
        # Should not return any artist
        self.check_query("ork1", [])

    def test_get_artist_list_parsed_query(self):
        """Test the parsed query."""
        self.authenticate(self.user)

        response = self.client.get(self.url, {"query": "none"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        query = response.data["query"]
        self.assertIn("remaining", query)

    def test_get_artist_list_with_query_empty(self):
        """Test to verify artist list with empty query."""
        # Login as simple user
        self.authenticate(self.user)

        # Get artists list with query = ""
        # Should return all artists
        self.check_query("", [self.artist1, self.artist2])

    def test_get_artist_list_with_query_no_keywords(self):
        """Test to verify artist query do not parse keywords."""
        # Login as simple user
        self.authenticate(self.user)

        # Get artists list with query = "title:Artist1"
        # Should not return anything since it searched for the whole string
        self.check_query("title:Artist1", [], ["title:Artist1"])

    def test_get_artists_list_with_query_multi_words(self):
        """Test query parse with multi words remaining."""
        # Login as simple user
        self.authenticate(self.user)

        # Get artists list with escaped space query
        # Should not return anything but check query
        self.check_query(
            r"word words\ words\ words remain",
            [],
            ["word", "words words words", "remain"],
        )

        # Get artists list with quoted query
        # Should not return anything but check query
        self.check_query(
            """ word"words words words" remain""",
            [],
            ["word", "words words words", "remain"],
        )

    def test_get_artists_list_with_query_two_words(self):
        """Test to search the intersection of two words in the query.

        Related to #192.
        """
        artist_names = ["hatsune miku", "hatsune", "miku"]
        for name in artist_names:
            Artist.objects.create(name=name)

        self.authenticate(self.user)

        # check that only the conjunction of the two words is found
        response = self.client.get(self.url, {"query": "hatsune miku"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)


class ArtistPruneViewAPIViewTestCase(LibraryAPITestCase):
    url = reverse("library-artist-prune")

    def setUp(self):
        # create a user without any rights
        self.user = self.create_user("TestUser", library_level="m")

        # create test data
        self.create_test_data()

    def test_delete(self):
        """Test to prune artists without songs."""
        # login as library manager
        self.authenticate(self.user)

        # check there are 2 artists
        self.assertEqual(Artist.objects.count(), 2)

        # prune artists
        response = self.client.delete(self.url)

        # check http status
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # check the response
        self.assertDictEqual(response.data, {"deleted_count": 1})

        # check there are only 1 artists remaining
        self.assertEqual(Artist.objects.count(), 1)

        # check artists with songs remains
        self.assertEqual(Artist.objects.filter(pk=self.artist2.pk).count(), 0)

    def test_delete_no_targets(self):
        """Test to prune artists when there are none to prune."""
        # login as library manager
        self.authenticate(self.user)

        # remove all artists
        Artist.objects.all().delete()

        # prune artists
        response = self.client.delete(self.url)

        # check http status
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # check the response
        self.assertDictEqual(response.data, {"deleted_count": 0})
