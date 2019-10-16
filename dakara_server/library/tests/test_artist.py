from django.core.urlresolvers import reverse
from rest_framework import status

from library.tests.base_test import LibraryAPITestCase


class ArtistListViewAPIViewTestCase(LibraryAPITestCase):
    url = reverse("library-artist-list")

    def setUp(self):
        # create a user without any rights
        self.user = self.create_user("TestUser")

        # create test data
        self.create_test_data()

    def test_get_artist_list(self):
        """Test to verify artist list with no query
        """
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
        """Test to verify unauthenticated user can't get artist list
        """
        # Attempt to get artists list
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_artist_list_with_query(self):
        """Test to verify artist list with query
        """
        # Login as simple user
        self.authenticate(self.user)

        # Get artists list with query = "tist1"
        # Should only return artist1
        self.artist_query_test("tist1", [self.artist1])

        # Get artists list with query = "ork1"
        # Should not return any artist
        self.artist_query_test("ork1", [])

    def test_get_artist_list_with_query_empty(self):
        """Test to verify artist list with empty query
        """
        # Login as simple user
        self.authenticate(self.user)

        # Get artists list with query = ""
        # Should return all artists
        self.artist_query_test("", [self.artist1, self.artist2])

    def test_get_artist_list_with_query_no_keywords(self):
        """Test to verify artist query do not parse keywords
        """
        # Login as simple user
        self.authenticate(self.user)

        # Get artists list with query = "title:Artist1"
        # Should not return anything since it searched for the whole string
        self.artist_query_test("title:Artist1", [], ["title:Artist1"])

    def test_get_artists_list_with_query__multi_words(self):
        """Test query parse with multi words remaining
        """
        # Login as simple user
        self.authenticate(self.user)

        # Get artists list with escaped space query
        # Should not return anything but check query
        self.artist_query_test(
            r"word words\ words\ words remain",
            [],
            ["word", "words words words", "remain"],
        )

        # Get artists list with quoted query
        # Should not return anything but check query
        self.artist_query_test(
            """ word"words words words" remain""",
            [],
            ["word", "words words words", "remain"],
        )

    def artist_query_test(self, query, expected_artists, remaining=None):
        """Method to test a artist request with a given query

        Returned artist should be the same as expected_artists,
        in the same order.
        """
        # TODO This only works when there is only one page of artists
        response = self.client.get(self.url, {"query": query})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], len(expected_artists))
        results = response.data["results"]
        self.assertEqual(len(results), len(expected_artists))
        for artist, expected_artist in zip(results, expected_artists):
            self.assertEqual(artist["id"], expected_artist.id)

        if remaining is not None:
            self.assertEqual(response.data["query"]["remaining"], remaining)
