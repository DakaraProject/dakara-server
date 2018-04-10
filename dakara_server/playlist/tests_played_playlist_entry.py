from django.core.urlresolvers import reverse
from rest_framework import status
from .base_test import BaseAPITestCase
from .models import PlaylistEntry

class PlaylistPlayedEntryListViewListAPIViewTestCase(BaseAPITestCase):
    url = reverse('playlist-played-entries-list')

    def setUp(self):
        self.create_test_data()

    def test_get_playlist_entries_list(self):
        """
        Test to verify playlist played entries list
        """
        # Login as simple user 
        self.authenticate(self.user)

        # Get playlist entries list 
        # Should only return entries with `was_played`=True
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(len(response.data['results']), 2)

        # Playlist entries are in order of creation
        self.check_playlist_played_entry_json(response.data['results'][0], self.pe3)
        self.check_playlist_played_entry_json(response.data['results'][1], self.pe4)

    def test_get_playlist_entries_list_forbidden(self):
        """
        Test to verify playlist entries list is not available when not logged in
        """
        # Get playlist entries list
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
