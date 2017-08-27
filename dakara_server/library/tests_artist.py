from django.core.urlresolvers import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from .base_test import BaseAPITestCase
from .models import *

UserModel = get_user_model()

class ArtistListAPIViewTestCase(BaseAPITestCase):
    url = reverse('library-artist-list')

    def setUp(self):
        # create a user without any rights
        self.user = self.create_user("TestUser")

        # create test data
        self.create_library_test_data()

    def test_get_artist_list(self):
        """
        Test to verify artist list with no query
        """
        # Login as simple user 
        self.authenticate(self.user)

        # Get artists list
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(len(response.data['results']), 2)

        # Artists are sorted by name
        self.check_artist_json(response.data['results'][0], self.artist1)
        self.check_artist_json(response.data['results'][1], self.artist2)

    def test_get_artist_list_forbidden(self):
        """
        Test to verify unauthenticated user can't get artist list 
        """
        # Attempt to get artists list
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_artist_list_with_query(self):
        """
        Test to verify artist list with query
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
        """
        Test to verify artist list with empty query
        """
        # Login as simple user 
        self.authenticate(self.user)

        # Get artists list with query = ""
        # Should return all artists
        self.artist_query_test("", [self.artist1, self.artist2])
