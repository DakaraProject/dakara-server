from django.core.urlresolvers import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from .base_test import BaseAPITestCase
from .models import *

UserModel = get_user_model()

class SongListAPIViewTestCase(BaseAPITestCase):
    url = reverse('library-song-list')

    def setUp(self):
        # create a user without any rights
        self.user = self.create_user("TestUser")

        # create test data
        self.create_library_test_data()

    def test_get_song_list(self):
        """
        Test to verify song list with no query
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
        """
        Test to verify unauthenticated user can't get songs list 
        """
        # Attempte to get songs list
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_song_list_with_query(self):
        """
        Test to verify song list with simple query
        """
        # Login as simple user 
        self.authenticate(self.user)

        # Get songs list with query = "ong1"
        # Should only return song1
        response = self.client.get(self.url, {'query': "ong1"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], "Song1")

        # Get songs list with query = "tist1"
        # Should only return song2 which has Artist1 as artist
        response = self.client.get(self.url, {'query': "tist1"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], "Song2")

        # Get songs list with query = "ork1"
        # Should only return song2 which is linked to Work1
        response = self.client.get(self.url, {'query': "ork1"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], "Song2")

    def test_get_song_list_with_query_tag(self):
        """
        Test to verify song list with tag query
        """
        # Login as simple user 
        self.authenticate(self.user)

        # Get songs list with query = "#TAG1"
        # Should only return song2
        response = self.client.get(self.url, {'query': "#TAG1"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], "Song2")

        # Get songs list with query = "#TAG2"
        # Should not return any result
        response = self.client.get(self.url, {'query': "#TAG2"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)
        self.assertEqual(len(response.data['results']), 0)

    def test_get_song_list_with_query_artist(self):
        """
        Test to verify song list with artist query
        """
        # Login as simple user 
        self.authenticate(self.user)

        # Get songs list with query = "artist:1"
        # Should only return song2
        response = self.client.get(self.url, {'query': "artist:1"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], "Song2")

        # Get songs list with query = "artist:k"
        # Should not return any result
        response = self.client.get(self.url, {'query': "artist:k"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)
        self.assertEqual(len(response.data['results']), 0)

        # Get songs list with query = "artist:""Artist1"""
        # Should only return song2
        response = self.client.get(self.url, {'query': "artist:\"\"Artist1\"\""})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], "Song2")

        # Get songs list with query = "artist:""tist1"""
        # Should not return any result
        response = self.client.get(self.url, {'query': "artist:\"\"tist1\"\""})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)
        self.assertEqual(len(response.data['results']), 0)

    def test_get_song_list_with_query_work(self):
        """
        Test to verify song list with work query
        """
        # Login as simple user 
        self.authenticate(self.user)

        # Get songs list with query = "wt1:Work1"
        # Should only return song2
        response = self.client.get(self.url, {'query': "wt1:Work1"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], "Song2")

        # Get songs list with query = "wt2:Work1"
        # Should not return any result since Work1 is not of type workType2
        response = self.client.get(self.url, {'query': "wt2:Work1"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)
        self.assertEqual(len(response.data['results']), 0)

    def test_get_song_list_with_query_title(self):
        """
        Test to verify song list with title query
        """
        # Login as simple user 
        self.authenticate(self.user)

        # Get songs list with query = "title:1"
        # Should only return song1
        response = self.client.get(self.url, {'query': "title:1"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], "Song1")

        # Get songs list with query = "title:Artist"
        # Should not return any result
        response = self.client.get(self.url, {'query': "title:Artist"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)
        self.assertEqual(len(response.data['results']), 0)
