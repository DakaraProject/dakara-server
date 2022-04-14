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
        self.check_playlist_played_entry_json(response.data["results"][0], self.pe3)
        self.check_playlist_played_entry_json(response.data["results"][1], self.pe4)

    def test_get_playlist_played_list_forbidden(self):
        """Test to verify playlist entries played list forbidden when not logged in."""
        # Get playlist entries list
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
