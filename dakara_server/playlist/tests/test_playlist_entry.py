from unittest.mock import patch
from datetime import datetime, timedelta

from django.urls import reverse
from django.utils.dateparse import parse_datetime
from rest_framework import status

from internal.tests.base_test import tz, UserModel
from playlist.models import PlaylistEntry, Player, Karaoke
from playlist.tests.base_test import PlaylistAPITestCase


class PlaylistEntryListViewListCreateAPIViewTestCase(PlaylistAPITestCase):
    url = reverse("playlist-entries-list")

    def setUp(self):
        self.create_test_data()

    @patch(
        "playlist.views.datetime",
        side_effect=lambda *args, **kwargs: datetime(*args, **kwargs),
    )
    def test_get_playlist_entries_list(self, mocked_datetime):
        """Test to verify playlist entries list
        """
        # patch the now method
        now = datetime.now(tz)
        mocked_datetime.now.return_value = now

        # Login as simple user
        self.authenticate(self.user)

        # Get playlist entries list
        # Should only return entries with `was_played`=False
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)

        # Playlist entries are in order of creation
        pe1 = response.data["results"][0]
        pe2 = response.data["results"][1]
        self.check_playlist_entry_json(pe1, self.pe1)
        self.check_playlist_entry_json(pe2, self.pe2)

        # check the date of the end of the playlist
        self.assertEqual(
            parse_datetime(response.data["date_end"]),
            now + self.pe1.song.duration + self.pe2.song.duration,
        )

        # check the date of play of each entries
        self.assertEqual(parse_datetime(pe1["date_play"]), now)
        self.assertEqual(parse_datetime(pe2["date_play"]), now + self.pe1.song.duration)

    @patch(
        "playlist.views.datetime",
        side_effect=lambda *args, **kwargs: datetime(*args, **kwargs),
    )
    def test_get_playlist_entries_list_while_playing(self, mocked_datetime):
        """Test to verify playlist entries play dates while playing

        The player is currently in the middle of the song, play dates should
        take account of the remaining time of the player.
        """
        # patch the now method
        now = datetime.now(tz)
        mocked_datetime.now.return_value = now

        # set the player
        player = Player.get_or_create()
        player.playlist_entry_id = self.pe1.id
        play_duration = timedelta(seconds=2)
        player.timing = play_duration
        player.save()

        # set the entry
        self.pe1.date_played = now - play_duration
        self.pe1.save()

        # Login as simple user
        self.authenticate(self.user)

        # Get playlist entries list
        # Should only return entries with `was_played`=False
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

        # Playlist entries are in order of creation
        pe2 = response.data["results"][0]
        self.check_playlist_entry_json(pe2, self.pe2)

        # check the date of play
        self.assertEqual(
            parse_datetime(response.data["date_end"]),
            now + self.pe1.song.duration - play_duration + self.pe2.song.duration,
        )

        # check the date of play of each entries
        self.assertEqual(
            parse_datetime(pe2["date_play"]),
            now + self.pe1.song.duration - play_duration,
        )

    def test_get_playlist_entries_list_forbidden(self):
        """Test to verify playlist entries list forbidden when not logged in
        """
        # Get playlist entries list
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch("playlist.views.broadcast_to_channel")
    def test_post_create_playlist_entry(self, mocked_broadcast_to_channel):
        """Test to verify playlist entry creation
        """
        # Login as playlist user
        self.authenticate(self.p_user)

        # Pre assert 4 entries in database
        self.assertEqual(PlaylistEntry.objects.count(), 4)

        # Post new playlist entry
        response = self.client.post(self.url, {"song_id": self.song1.id})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check playlist entry has been created in database
        self.assertEqual(PlaylistEntry.objects.count(), 5)
        new_entry = PlaylistEntry.objects.last()
        # Entry was created with for song1
        self.assertEqual(new_entry.song, self.song1)
        # Entry's owner is the user who created it
        self.assertEqual(new_entry.owner, self.p_user)

        # check the player was not requested to play this entry immediately
        mocked_broadcast_to_channel.assert_not_called()

    @patch("playlist.views.broadcast_to_channel")
    def test_post_create_playlist_entry_empty(self, mocked_broadcast_to_channel):
        """Test to create a playlist entry when the playlist is empty

        The created song should be requested to play immediately.
        """
        # empty the playlist
        PlaylistEntry.objects.all().delete()

        # Login as playlist user
        self.authenticate(self.p_user)

        # Post new playlist entry
        response = self.client.post(self.url, {"song_id": self.song1.id})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check playlist entry has been created in database
        self.assertEqual(PlaylistEntry.objects.count(), 1)
        new_entry = PlaylistEntry.objects.last()
        # Entry was created with for song1
        self.assertEqual(new_entry.song, self.song1)
        # Entry's owner is the user who created it
        self.assertEqual(new_entry.owner, self.p_user)

        # check the player was requested to play this entry immediately
        mocked_broadcast_to_channel.assert_called_with(
            "playlist.device", "send_playlist_entry", {"playlist_entry": new_entry}
        )

    def test_post_create_playlist_entry_not_ongoing_forbidden(self):
        """Test to verify playlist entry cannot be created when kara not ongoing
        """
        # Set karaoke not ongoing
        self.set_karaoke(ongoing=False)

        # Login as playlist manager
        self.authenticate(self.manager)

        # Post new playlist entry
        response = self.client.post(self.url, {"song_id": self.song1.id})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_post_create_playlist_entry_cant_add_to_playlist_forbidden_user(self):
        """Test to verify playlist entry cannot be created when can't add to playlist
        """
        # Set can't add to playlist
        self.set_karaoke(can_add_to_playlist=False)

        # Login as playlist user
        self.authenticate(self.user)

        # Post new playlist entry
        response = self.client.post(self.url, {"song_id": self.song1.id})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_post_create_playlist_entry_cant_add_to_playlist_allowed_manager(self):
        """Test to verify playlist entry cannot be created when can't add to playlist
        """
        # Set can't add to playlist
        self.set_karaoke(can_add_to_playlist=False)

        # Login as playlist user
        self.authenticate(self.manager)

        # Post new playlist entry
        response = self.client.post(self.url, {"song_id": self.song1.id})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @patch("playlist.views.settings")
    def test_post_create_playlist_entry_playlist_full_forbidden(self, mock_settings):
        """Test to verify playlist entry creation
        """
        # mock the settings
        mock_settings.PLAYLIST_SIZE_LIMIT = 1

        # Login as playlist user
        self.authenticate(self.p_user)

        # Pre assert 4 entries in database
        # (2 in queue)
        self.assertEqual(PlaylistEntry.objects.count(), 4)

        # Post new playlist entry
        response = self.client.post(self.url, {"song_id": self.song1.id})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # post assert there are still 4 in database
        self.assertEqual(PlaylistEntry.objects.count(), 4)

    def test_post_create_playlist_entry_date_stop_success(self):
        """Test user can add a song to playlist when before date stop
        """
        # set kara stop
        date_stop = datetime.now(tz) + timedelta(hours=2)
        karaoke = Karaoke.get_object()
        karaoke.date_stop = date_stop
        karaoke.save()

        # login as user
        self.authenticate(self.p_user)

        # pre assert
        self.assertEqual(PlaylistEntry.objects.count(), 4)

        # request to add a new entry
        response = self.client.post(self.url, {"song_id": self.song1.id})

        # assert that the request is accepted
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(PlaylistEntry.objects.count(), 5)

    def test_post_create_playlist_entry_date_stop_forbidden(self):
        """Test user cannot add song to playlist after its date stop
        """
        # set kara stop
        date_stop = datetime.now(tz)
        karaoke = Karaoke.get_object()
        karaoke.date_stop = date_stop
        karaoke.save()

        # login as user
        self.authenticate(self.p_user)

        # pre assert
        self.assertEqual(PlaylistEntry.objects.count(), 4)

        # request to add a new entry
        response = self.client.post(self.url, {"song_id": self.song1.id})

        # assert that the request is denied
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(PlaylistEntry.objects.count(), 4)

    def test_post_create_playlist_entry_date_stop_success_manager(self):
        """Test manager can add song to playlist after its date stop
        """
        # set kara stop
        date_stop = datetime.now(tz)
        karaoke = Karaoke.get_object()
        karaoke.date_stop = date_stop
        karaoke.save()

        # login as manager
        self.authenticate(self.manager)

        # pre assert
        self.assertEqual(PlaylistEntry.objects.count(), 4)

        # request to add a new entry
        response = self.client.post(self.url, {"song_id": self.song1.id})

        # assert that the response and the database
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(PlaylistEntry.objects.count(), 5)

    def test_post_create_playlist_entry_date_stop_success_admin(self):
        """Test admin can add song to playlist after its date stop
        """
        # set kara stop
        date_stop = datetime.now(tz)
        karaoke = Karaoke.get_object()
        karaoke.date_stop = date_stop
        karaoke.save()

        # login as admin
        self.authenticate(self.admin)

        # pre assert
        self.assertEqual(PlaylistEntry.objects.count(), 4)

        # request to add a new entry
        response = self.client.post(self.url, {"song_id": self.song1.id})

        # assert that the response and the database
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(PlaylistEntry.objects.count(), 5)

    @patch(
        "playlist.views.datetime",
        side_effect=lambda *args, **kwargs: datetime(*args, **kwargs),
    )
    def test_post_create_playlist_entry_date_stop_forbidden_playlist_playing(
        self, mocked_datetime
    ):
        """Test user cannot add song to playlist after its date stop

        Test that only short enough songs can be added.
        Test when the player is playing.
        """
        # patch the now method
        now = datetime.now(tz)
        mocked_datetime.now.return_value = now

        # set the player
        self.player_play_next_song(timing=timedelta(seconds=2))

        # set kara stop such as to allow song1 to be added and not song2
        date_stop = now + timedelta(seconds=20)
        karaoke = Karaoke.get_object()
        karaoke.date_stop = date_stop
        karaoke.save()

        # login as user
        self.authenticate(self.p_user)

        # pre assert
        self.assertEqual(PlaylistEntry.objects.count(), 4)

        # request to add a new entry which is too long
        response = self.client.post(self.url, {"song_id": self.song2.id})

        # assert that the request is denied
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(PlaylistEntry.objects.count(), 4)

        # request to add a new entry which is short enough
        response = self.client.post(self.url, {"song_id": self.song1.id})

        # assert that the request is denied
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(PlaylistEntry.objects.count(), 5)

    def test_post_create_user_forbidden(self):
        """Test to verify simple user cannot create playlist entries
        """
        # Login as simple user
        self.authenticate(self.user)

        # Attempt to post new playlist entry
        response = self.client.post(self.url, {"song_id": self.song1.id})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_post_create_user_unauthenticated_forbidden(self):
        """Test to verify unauthenticated user cannot create playlist entries
        """
        # Attempt to post new playlist entry
        response = self.client.post(self.url, {"song_id": self.song1.id})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_playlist_entries_list_playing_entry(self):
        """Test to verify playlist entries list does not include playing song
        """
        # Login as simple user
        self.authenticate(self.user)

        # pre assert
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)

        # Simulate a player playing next song
        self.player_play_next_song()

        # Get playlist entries list
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

        # Playlist entries are in order of creation
        self.check_playlist_entry_json(response.data["results"][0], self.pe2)

    def test_post_create_playlist_entry_disabled_tag(self):
        """Test playlist entry creation for a song with a disabled tag

        The creation is forbidden.
        """
        # Login as playlist user
        self.authenticate(self.p_user)

        # Set tag1 disabled
        self.tag1.disabled = True
        self.tag1.save()

        # Post new playlist entry with disabled Tag 1
        response = self.client.post(self.url, {"song_id": self.song1.id})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_post_create_playlist_entry_disabled_tag_manager(self):
        """Test playlist entry for song with a disabled tag if manager

        The user is manager for playlist and library, the creation is allowed.
        """
        # Login as playlist user
        user = self.create_user(
            "manager", playlist_level=UserModel.MANAGER, library_level=UserModel.MANAGER
        )
        self.authenticate(user)

        # Set tag1 disabled
        self.tag1.disabled = True
        self.tag1.save()

        # Post new playlist entry with disabled Tag 1
        response = self.client.post(self.url, {"song_id": self.song1.id})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class PlaylistEntryViewDestroyAPIViewTestCase(PlaylistAPITestCase):
    def setUp(self):
        self.create_test_data()

        # Create urls to access these playlist entries
        self.url_pe1 = reverse("playlist-entries-detail", kwargs={"pk": self.pe1.id})
        self.url_pe2 = reverse("playlist-entries-detail", kwargs={"pk": self.pe2.id})
        self.url_pe3 = reverse("playlist-entries-detail", kwargs={"pk": self.pe3.id})

    def test_delete_playlist_entry_manager(self):
        """Test to verify playlist entry deletion as playlist manager
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
        """Test to verify playlist entry deletion as playlist user
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
        """Test to verify playing entry can not be deleted
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
        """Test to verify already played entry can not be deleted
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

    def test_put_playlist_reorder_before(self):
        """Test playlist reorder before another entry
        """
        # Login as manager
        self.authenticate(self.manager)

        # Pre-assertion: order pe1, pe2
        playlist = list(PlaylistEntry.objects.exclude(was_played=True))
        self.assertListEqual(playlist, [self.pe1, self.pe2])

        # Reorder pe2 before pe1
        response = self.client.put(self.url_pe2, data={"before_id": self.pe1.id})

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Check new order pe2, pe1
        playlist = list(PlaylistEntry.objects.exclude(was_played=True))
        self.assertListEqual(playlist, [self.pe2, self.pe1])

    def test_put_playlist_reorder_after(self):
        """Test playlist reorder after another entry
        """
        # Login as manager
        self.authenticate(self.manager)

        # Pre-assertion: order pe1, pe2
        playlist = list(PlaylistEntry.objects.exclude(was_played=True))
        self.assertListEqual(playlist, [self.pe1, self.pe2])

        # Reorder pe1 after pe2
        response = self.client.put(self.url_pe1, data={"after_id": self.pe2.id})

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Check new order pe2, pe1
        playlist = list(PlaylistEntry.objects.exclude(was_played=True))
        self.assertListEqual(playlist, [self.pe2, self.pe1])

    def test_put_playlist_reorder_entry_played(self):
        """Test cannot reorder before played entry
        """
        # Login as manager
        self.authenticate(self.manager)

        # Attempt to reorder pe2 before pe3
        response = self.client.put(self.url_pe2, data={"before_id": self.pe3.id})

        # Played entry not found
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_put_playlist_reorder_entry_playing(self):
        """Test cannot reorder before played entry
        """
        # Simulate a player playing next song (pe1)
        self.player_play_next_song()

        # Login as manager
        self.authenticate(self.manager)

        # Attempt to reorder pe2 before pe1
        response = self.client.put(self.url_pe2, data={"before_id": self.pe1.id})

        # Played entry not found
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_put_playlist_reorder_forbidden(self):
        """Test user cannot reorder playlist
        """
        # Login as user
        self.authenticate(self.p_user)

        # Attempt to reorder pe2 before pe1
        response = self.client.put(self.url_pe2, data={"before_id": self.pe1.id})

        # Played entry not found
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_put_playlist_reorder_entry_after_and_before(self):
        """Test cannot reorder with both before and after
        """
        # Login as manager
        self.authenticate(self.manager)

        # Attempt to reorder pe2 before and after pe1
        response = self.client.put(
            self.url_pe2, data={"before_id": self.pe1.id, "after_id": self.pe1.id}
        )

        # Validation error
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_put_playlist_reorder_no_fields(self):
        """Test cannot reorder with no fields
        """
        # Login as manager
        self.authenticate(self.manager)

        # Attempt to reorder pe2 with nothing
        response = self.client.put(self.url_pe2, data={})

        # Validation error
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
