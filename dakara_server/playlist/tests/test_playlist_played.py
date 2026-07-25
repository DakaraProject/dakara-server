from datetime import datetime

from django.urls import reverse
from rest_framework import status

from internal.tests.base_test import UserModel, tz
from playlist.models import PlaylistEntry
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

        response0 = self.check_query("ong1", [self.pe4])

        self.assertCountEqual(response0.data["query"]["remaining"], ["ong1"])

        response1 = self.check_query("anager", [self.pe3])

        self.assertCountEqual(response1.data["query"]["remaining"], ["anager"])

    def test_get_playlist_played_list_with_query_id(self):
        """Search playlist entries played list by id."""
        self.authenticate(self.user)

        self.check_query("id:4", [self.pe4])

    def test_get_playlist_played_list_with_query_song_title(self):
        """Search playlist entries played list by song title."""
        self.authenticate(self.user)

        self.check_query("title: song1", [self.pe4])

    def test_get_playlist_played_list_with_query_owner(self):
        """Search playlist entries played list by owner."""
        self.authenticate(self.user)

        self.check_query("owner:manager", [self.pe3])
        self.check_query('owner:"manager"', [self.pe3])
        self.check_query('owner:""testPlaylistManager""', [self.pe3])
        self.check_query("owner:user", [self.pe4])

    def test_get_playlist_played_list_two_words(self):
        """Test to search the intersection of two words in the query.

        Related to #192.
        """
        user_names = ["hatsune miku", "hatsune", "miku"]
        for name in user_names:
            user = self.create_user(name, playlist_level=UserModel.USER)
            PlaylistEntry.objects.create(
                song=self.song1,
                owner=user,
                was_played=True,
                date_play=datetime.now(tz),
            )

        self.authenticate(self.user)

        # check that only the conjunction of the two words is found
        response = self.client.get(self.url, {"query": "hatsune miku"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

        # check that only the conjunction of the two words is found (reverse)
        response = self.client.get(self.url, {"query": "miku hatsune"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
