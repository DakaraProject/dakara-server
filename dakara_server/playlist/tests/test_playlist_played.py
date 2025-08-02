from django.urls import reverse
from rest_framework import status

from playlist.tests.base_test import PlaylistAPITestCase


class PlaylistPlayedListViewTestCase(PlaylistAPITestCase):
    url = reverse("playlist-played-list")

    def setUp(self):
        self.create_test_data()

    def test_get_playlist_played_list(self):
        """Test to verify playlist entries played list."""
        # Login as simple user
        self.authenticate(self.user)

        # Get playlist entries list
        # Should only return entries with `was_played`=True
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)
        self.assertEqual(len(response.data["results"]), 2)

        # Playlist entries are in order of creation
        self.check_playlist_played_entry_json(response.data["results"][0], self.pe4)
        self.check_playlist_played_entry_json(response.data["results"][1], self.pe3)

    def test_get_playlist_played_list_forbidden(self):
        """Test to verify playlist entries played list forbidden when not logged in."""
        # Get playlist entries list
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_playlist_played_list_with_query(self):
        """Search playlist entries played list with simple query."""
        self.authenticate(self.user)

        self.entries_query_test("ong1", [self.pe4])

    def test_get_playlist_played_list_with_query_song_title(self):
        """Search playlist entries played list by song title."""
        self.authenticate(self.user)

        self.entries_query_test("title: song1", [self.pe4])

    def test_get_playlist_played_list_with_query_owner(self):
        """Search playlist entries played list by owner."""
        self.authenticate(self.user)

        self.entries_query_test("owner: manager", [self.pe3])
        self.entries_query_test("owner: user", [self.pe4])

    def entries_query_test(self, query, expected_entries):
        """Method to test an entry request with a given query.

        Returned entries should be the same as `expected_entries`, in the same
        order.
        """
        response = self.client.get(self.url, {"query": query})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], len(expected_entries))
        results = response.data["results"]
        self.assertEqual(len(results), len(expected_entries))
        for entry, expected_entry in zip(results, expected_entries):
            self.assertEqual(entry["id"], expected_entry.id)
