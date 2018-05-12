from django.core.urlresolvers import reverse
from rest_framework import status

from .base_test import BaseAPITestCase


class SongListViewAPIViewTestCase(BaseAPITestCase):
    url = reverse('library-song-list')

    def setUp(self):
        # create a user without any rights
        self.user = self.create_user("TestUser")

        # create a manager
        self.manager = self.create_user("TestManager", library_level='m')

        # create test data
        self.create_library_test_data()

    def test_get_song_list(self):
        """Test to verify song list with no query
        """
        # Login as simple user
        self.authenticate(self.user)

        # Get songs list
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(len(response.data['results']), 2)

        # Songs are sorted by title
        self.check_song_json(response.data['results'][0], self.song1)
        self.check_song_json(response.data['results'][1], self.song2)

    def test_get_song_list_forbidden(self):
        """Test to verify unauthenticated user can't get songs list
        """
        # Attempte to get songs list
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_song_list_with_query(self):
        """Test to verify song list with simple query
        """
        # Login as simple user
        self.authenticate(self.user)

        # Get songs list with query = "ong1"
        # Should only return song1
        self.song_query_test("ong1", [self.song1])

        # Get songs list with query = "tist1"
        # Should only return song2 which has Artist1 as artist
        self.song_query_test("tist1", [self.song2])

        # Get songs list with query = "ork1"
        # Should only return song2 which is linked to Work1
        self.song_query_test("ork1", [self.song2])

        # Get songs list with query = "Version2"
        # Should only return song2
        self.song_query_test("ersion2", [self.song2])

        # Get songs list with query = "Detail2"
        # Should only return song2
        self.song_query_test("etail2", [self.song2])

        # Get songs list with query = "Detail_Video2"
        # Should only return song2
        self.song_query_test("etail_Video2", [self.song2])


    def test_get_song_list_with_query_empty(self):
        """Test to verify song list with empty query
        """
        # Login as simple user
        self.authenticate(self.user)

        # Get songs list with query = ""
        # Should return all songs
        self.song_query_test("", [self.song1, self.song2])

    def test_get_song_list_with_query_tag(self):
        """Test to verify song list with tag query
        """
        # Login as simple user
        self.authenticate(self.user)

        # Get songs list with query = "#TAG1"
        # Should only return song2
        self.song_query_test("#TAG1", [self.song2])

        # Get songs list with query = "#TAG2"
        # Should not return any result
        self.song_query_test("#TAG2", [])

    def test_get_song_list_with_query_artist(self):
        """Test to verify song list with artist query
        """
        # Login as simple user
        self.authenticate(self.user)

        # Get songs list with query = "artist:1"
        # Should only return song2
        self.song_query_test("artist:1", [self.song2])

        # Get songs list with query = "artist:k"
        # Should not return any result
        self.song_query_test("artist:k", [])

        # Get songs list with query = "artist:""Artist1"""
        # Should only return song2
        self.song_query_test("artist:\"\"Artist1\"\"", [self.song2])

        # Get songs list with query = "artist:""tist1"""
        # Should not return any result
        self.song_query_test("artist:\"\"tist1\"\"", [])

    def test_get_song_list_with_query_work(self):
        """Test to verify song list with work query
        """
        # Login as simple user
        self.authenticate(self.user)

        # Get songs list with query = "wt1:Work1"
        # Should only return song2
        self.song_query_test("wt1:Work1", [self.song2])

        # Get songs list with query = "wt1:""Work1"""
        # Should only return song2
        self.song_query_test("""wt1:""Work1"" """, [self.song2])

        # Get songs list with query = "wt2:Work1"
        # Should not return any result since Work1 is not of type workType2
        self.song_query_test("wt2:Work1", [])

    def test_get_song_list_with_query_title(self):
        """Test to verify song list with title query
        """
        # Login as simple user
        self.authenticate(self.user)

        # Get songs list with query = "title:1"
        # Should only return song1
        self.song_query_test("title:1", [self.song1])

        # Get songs list with query = "title:""Song1"""
        # Should only return song1
        self.song_query_test(""" title:""Song1"" """, [self.song1])

        # Get songs list with query = "title:Artist"
        # Should not return any result
        self.song_query_test("title:Artist", [])

    def test_get_song_list_with_query_multiple(self):
        """Test to verify song list with title query
        """
        # Login as simple user
        self.authenticate(self.user)

        # Get songs list with query = "artist:Artist1 title:1"
        # Should not return any song
        self.song_query_test("artist:Artist1 title:1", [])

    def test_get_song_list_with_query_complex(self):
        """Test to verify parsed query is returned
        """
        # Login as simple user
        self.authenticate(self.user)

        query = (
            """hey  artist: me work:you wt1:workName title: test\ Test """
            """remain stuff #tagg wt3:test artist:"my artist" work:""exact """
            """Work"" i   """
        )

        # Get song list with a complex query
        # should not return any song, but we'll check returned parsed query
        response = self.client.get(self.url, {'query': query})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)
        results = response.data['results']
        self.assertEqual(len(results), 0)
        query = response.data['query']
        self.assertCountEqual(
            query['remaining'], [
                'remain', 'stuff', 'hey', 'i', 'wt3:test'])
        self.assertCountEqual(query['tag'], ['TAGG'])
        self.assertCountEqual(query['title']['contains'], ['test Test'])
        self.assertCountEqual(query['title']['exact'], [])
        self.assertCountEqual(query['artist']['contains'], ['me', 'my artist'])
        self.assertCountEqual(query['artist']['exact'], [])
        self.assertCountEqual(query['work']['contains'], ['you'])
        self.assertCountEqual(query['work']['exact'], ["exact Work"])
        self.assertCountEqual(query['work_type'].keys(), ['wt1'])
        self.assertCountEqual(
            query['work_type']['wt1']['contains'],
            ['workName'])
        self.assertCountEqual(query['work_type']['wt1']['exact'], [])

    def song_query_test(self, query, expected_songs):
        """Method to test a song request with a given query

        Returned songs should be the same as expected_songs,
        in the same order.
        """
        # TODO This only works when there is only one page of songs
        response = self.client.get(self.url, {'query': query})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], len(expected_songs))
        results = response.data['results']
        self.assertEqual(len(results), len(expected_songs))
        for song, expected_song in zip(results, expected_songs):
            self.assertEqual(song['id'], expected_song.id)

    def test_get_song_list_disabled_tag(self):
        """Test to verify songs with disabled for user

        For a simple user, song list does not include disabled songs with tags.
        """
        # Login as simple user
        self.authenticate(self.user)

        # Set tag1 disabled
        self.tag1.disabled = True
        self.tag1.save()

        # Get songs list, there should be only one song
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(len(response.data['results']), 1)

        # The remaining song is Song1
        # Song2 has been excluded from the list
        self.check_song_json(response.data['results'][0], self.song1)

    def test_get_song_list_disabled_tag_manager(self):
        """Test to verify songs with disabled tags for manager

        For a manager, song list includes disabled songs with tags.
        """
        # Login as simple user
        self.authenticate(self.manager)

        # Set tag1 disabled
        self.tag1.disabled = True
        self.tag1.save()

        # Get songs list, there should be only one song
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(len(response.data['results']), 2)

        # The remaining song is Song1
        # Song2 has been excluded from the list
        self.check_song_json(response.data['results'][0], self.song1)
        self.check_song_json(response.data['results'][1], self.song2)
