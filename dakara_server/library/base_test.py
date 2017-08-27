from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase
from rest_framework import status
from .models import *

UserModel = get_user_model()
class BaseAPITestCase(APITestCase):

    def authenticate(self, user):
        token = Token.objects.create(user=user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

    def create_user(self, username, playlist_level=None, library_level=None, users_level=None):
        user = UserModel.objects.create_user(username, "", "password")
        user.playlist_permission_level = playlist_level
        user.library_permission_level = library_level
        user.users_permission_level = users_level
        user.save()
        return user

    def create_library_test_data(self):
        # Create work types
        self.wt1 = WorkType(name="WorkType1", query_name="wt1")
        self.wt1.save()
        self.wt2 = WorkType(name="WorkType2", query_name="wt2")
        self.wt2.save()

        # Create works
        self.work1 = Work(title="Work1", work_type=self.wt1)
        self.work1.save()
        self.work2 = Work(title="Work2", work_type=self.wt1)
        self.work2.save()
        self.work3 = Work(title="Work3", work_type=self.wt2)
        self.work3.save()

        # Create artists
        self.artist1 = Artist(name="Artist1")
        self.artist1.save()
        self.artist2 = Artist(name="Artist2")
        self.artist2.save()

        # Create song tags
        self.tag1 = SongTag(name="TAG1")
        self.tag1.save()
        self.tag2 = SongTag(name="TAG2")
        self.tag2.save()

        # Create songs

        # Song with no tag, artist or work
        self.song1 = Song(title="Song1", filename="file.mp4")
        self.song1.save()

        # Song associated with work, artist, and tag
        self.song2 = Song(title="Song2", filename="file.mp4")
        self.song2.save()
        self.song2.tags.add(self.tag1)
        self.song2.artists.add(self.artist1)
        SongWorkLink(
                song_id=self.song2.id,
                work_id=self.work1.id,
                link_type=SongWorkLink.OPENING
                ).save()

    def check_song_json(self, json, expected_song):
        """
        Method to test a song representation against the expected song
        """
        self.assertEqual(json['id'], expected_song.id)
        self.assertEqual(json['title'], expected_song.title)
        self.assertEqual(json['filename'], expected_song.filename)
        self.assertEqual(json['directory'], expected_song.directory)
        self.assertEqual(json['version'], expected_song.version)
        self.assertEqual(json['detail'], expected_song.detail)
        self.assertEqual(json['detail_video'], expected_song.detail_video)

    def check_artist_json(self, json, expected_song):
        """
        Method to test an representation against the expected artist
        """
        self.assertEqual(json['id'], expected_song.id)
        self.assertEqual(json['name'], expected_song.name)

    def song_query_test(self, query, expected_songs):
        """
        Method to test a song request with a given query
        Returned songs should be the same as expected_songs,
        in the same order
        """
        # TODO This only works when there is only one page of songs
        response = self.client.get(self.url, {'query': query})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], len(expected_songs))
        results = response.data['results']
        self.assertEqual(len(results), len(expected_songs))
        for song, expected_song in zip(results, expected_songs):
            self.assertEqual(song['id'], expected_song.id)

    def artist_query_test(self, query, expected_artists):
        """
        Method to test a artist request with a given query
        Returned artist should be the same as expected_artists,
        in the same order
        """
        # TODO This only works when there is only one page of artists
        response = self.client.get(self.url, {'query': query})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], len(expected_artists))
        results = response.data['results']
        self.assertEqual(len(results), len(expected_artists))
        for artist, expected_artist in zip(results, expected_artists):
            self.assertEqual(artist['id'], expected_artist.id)
