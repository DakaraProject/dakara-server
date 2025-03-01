from django.urls import reverse
from rest_framework import status

from playlist.models import Karaoke, PlayerToken
from playlist.tests.base_test import PlaylistAPITestCase


class PlayerTokenListViewTestCase(PlaylistAPITestCase):
    url = reverse("playlist-player-token-list")

    def setUp(self):
        self.create_test_data()

    def test_create(self):
        """Test to create a token"""
        # get karaoke
        karaoke = Karaoke.objects.get_object()

        # pre assert there are no player tokens
        self.assertEqual(PlayerToken.objects.count(), 0)

        # login
        self.authenticate(self.manager)

        # create the token
        response = self.client.post(self.url, {"karaoke": karaoke.id})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # check the token exists
        self.assertEqual(PlayerToken.objects.count(), 1)
        player_token = PlayerToken.objects.get(pk=karaoke.id)
        self.assertIsNotNone(player_token.key)
        self.assertEqual(len(player_token.key), 40)


class PlayerTokenViewTestCase(PlaylistAPITestCase):
    def setUp(self):
        self.create_test_data()

    def test_get(self):
        """Test to get a token"""
        # get karaoke and token
        karaoke = Karaoke.objects.get_object()
        player_token = PlayerToken.objects.create(karaoke=karaoke)
        self.assertEqual(len(player_token.key), 40)

        # login
        self.authenticate(self.manager)

        # get the token
        url = reverse("playlist-player-token", kwargs={"pk": karaoke.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # check the token
        self.assertEqual(len(response.data["key"]), 40)
        self.assertEqual(response.data["key"], player_token.key)

        self.assertEqual(response.data["karaoke_id"], player_token.karaoke.id)

    def test_delete(self):
        """Test to delete a token"""
        # get karaoke and token
        karaoke = Karaoke.objects.get_object()
        PlayerToken.objects.create(karaoke=karaoke)

        # login
        self.authenticate(self.manager)

        # delete the token
        url = reverse("playlist-player-token", kwargs={"pk": karaoke.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # check there are no token
        self.assertEqual(PlayerToken.objects.count(), 0)
