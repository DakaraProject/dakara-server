from django.core.urlresolvers import reverse
from rest_framework import status
from .base_test import BaseAPITestCase
from .models import PlaylistEntry

class PlaylistEntryListViewListCreateAPIViewTestCase(BaseAPITestCase):
    url = reverse('playlist-entries-list')

    def setUp(self):
        self.create_test_data()

    def test_get_playlist_entries_list(self):
        """
        Test to verify playlist entries list
        """
        # Login as simple user 
        self.authenticate(self.user)

        # Get playlist entries list 
        # Should only return entries with `was_played`=False
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(len(response.data['results']), 2)

        # Playlist entries are in order of creation
        self.check_playlist_entry_json(response.data['results'][0], self.pe1)
        self.check_playlist_entry_json(response.data['results'][1], self.pe2)

    def test_get_playlist_entries_list_forbidden(self):
        """
        Test to verify playlist entries list is not available when not logged in
        """
        # Get playlist entries list
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_post_create_playlist_entry(self):
        """
        Test to verify playlist entry creation
        """
        # Login as playlist user
        self.authenticate(self.p_user)

        # Pre assert 4 entries in database
        self.assertEqual(PlaylistEntry.objects.count(), 4)

        # Post new playlist entry
        response = self.client.post(self.url, {"song": self.song1.id})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check playlist entry has been created in database
        self.assertEqual(PlaylistEntry.objects.count(), 5)
        new_entry = PlaylistEntry.objects.order_by('-date_created')[0]
        # Entry was created with for song1
        self.assertEqual(new_entry.song.id, self.song1.id)
        # Entry's owner is the user who created it
        self.assertEqual(new_entry.owner.id, self.p_user.id)

    def test_post_create_playlist_entry_kara_status_stop_forbidden(self):
        """
        Test to verify playlist entry cannot be created when kara is stopped
        """
        # stop kara
        self.set_kara_status_stop()

        # Login as playlist user
        self.authenticate(self.manager)

        # Post new playlist entry
        response = self.client.post(self.url, {"song": self.song1.id})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_post_create_user_forbidden(self):
        """
        Test to verify simple user cannot create playlist entries
        """
        # Login as simple user 
        self.authenticate(self.user)

        # Attempt to post new playlist entry
        response = self.client.post(self.url, {"song": self.song1.id})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_playlist_entries_list_playing_entry(self):
        """
        Test to verify playlist entries list does not include playing song
        """
        # Simulate a player playing next song
        self.player_play_next_song()

        # Login as simple user 
        self.authenticate(self.user)

        # Get playlist entries list 
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(len(response.data['results']), 1)

        # Playlist entries are in order of creation
        self.check_playlist_entry_json(response.data['results'][0], self.pe2)

    def test_post_create_playlist_entry_disabled_tag(self):
        """
        Test to verify playlist entry creation is forbidden for a song with a
        disabled tag
        """
        # Login as playlist user
        self.authenticate(self.p_user)

        # Set tag1 disabled
        self.tag1.disabled = True
        self.tag1.save()

        # Post new playlist entry with disabled Tag 1
        response = self.client.post(self.url, {"song": self.song1.id})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_post_create_playlist_entry_disabled_tag_manager(self):
        """
        Test to verify playlist entry creation is allowed for a song with a
        disabled tag when the user is manager for playlist and library
        """
        # Login as playlist user
        user = self.create_user('manager', playlist_level='m',
                                library_level='m')
        self.authenticate(user)

        # Set tag1 disabled
        self.tag1.disabled = True
        self.tag1.save()

        # Post new playlist entry with disabled Tag 1
        response = self.client.post(self.url, {"song": self.song1.id})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

class PlaylistEntryViewDestroyAPIViewTestCase(BaseAPITestCase):

    def setUp(self):
        self.create_test_data()

        # Create urls to access these playlist entries
        self.url_pe1 = reverse('playlist-entries-detail', kwargs={"pk": self.pe1.id})
        self.url_pe2 = reverse('playlist-entries-detail', kwargs={"pk": self.pe2.id})
        self.url_pe3 = reverse('playlist-entries-detail', kwargs={"pk": self.pe3.id})


    def test_delete_playlist_entry_manager(self):
        """
        Test to verify playlist entry deletion as playlist manager
        """
        # Login as playlist manager
        self.authenticate(self.manager)

        # Pre assert 4 entries in database
        self.assertEqual(PlaylistEntry.objects.count(), 4)

        # Delete playlist entries created by manager
        response = self.client.delete(self.url_pe1)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # This playlist entry has been removed from database
        self.assertEqual(PlaylistEntry.objects.count(), 3)
        entries = PlaylistEntry.objects.filter(id=self.pe1.id)
        self.assertEqual(len(entries), 0)

        # Delete playlist entries created by other user
        response = self.client.delete(self.url_pe2)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # This playlist entry has been removed from database
        self.assertEqual(PlaylistEntry.objects.count(), 2)

    def test_delete_playlist_entry_playlist_user(self):
        """
        Test to verify playlist entry deletion as playlist user
        """
        # Login as playlist user
        self.authenticate(self.p_user)

        # Pre assert 4 entries in database
        self.assertEqual(PlaylistEntry.objects.count(), 4)

        # Delete playlist entries created by self
        response = self.client.delete(self.url_pe2)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # This playlist entry has been removed from database
        self.assertEqual(PlaylistEntry.objects.count(), 3)
        entries = PlaylistEntry.objects.filter(id=self.pe2.id)
        self.assertEqual(len(entries), 0)

        # Attempt to delete playlist entry created by other user
        response = self.client.delete(self.url_pe1)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_playlist_entry_playing(self):
        """
        Test to verify playing entry can not be deleted
        """
        # Simulate a player playing next song
        self.player_play_next_song()

        # Login as playlist manager
        self.authenticate(self.manager)

        # Pre assert 4 entries in database
        self.assertEqual(PlaylistEntry.objects.count(), 4)

        # Attempt to delete playing entry 
        response = self.client.delete(self.url_pe1)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # This playlist entry is still there
        self.assertEqual(PlaylistEntry.objects.count(), 4)
        entries = PlaylistEntry.objects.filter(id=self.pe1.id)
        self.assertEqual(len(entries), 1)

    def test_delete_playlist_entry_played(self):
        """
        Test to verify already played entry can not be deleted
        """
        # Login as playlist manager
        self.authenticate(self.manager)

        # Pre assert 4 entries in database
        self.assertEqual(PlaylistEntry.objects.count(), 4)

        # Attempt to delete already played entry 
        response = self.client.delete(self.url_pe3)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # This playlist entry is still there
        self.assertEqual(PlaylistEntry.objects.count(), 4)
        entries = PlaylistEntry.objects.filter(id=self.pe3.id)
        self.assertEqual(len(entries), 1)
