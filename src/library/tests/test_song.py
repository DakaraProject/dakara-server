from datetime import timedelta

from django.urls import reverse
from rest_framework import status

from internal.tests.base_test import UserModel
from library.models import Artist, Song, SongTag, SongWorkLink, Work
from library.tests.base_test import LibraryAPITestCase


class SongListViewTestCase(LibraryAPITestCase):
    url = reverse("library-song-list")

    def setUp(self):
        # create a user without any rights
        self.user = self.create_user("TestUser")

        # create a manager
        self.manager = self.create_user("TestManager", library_level=UserModel.MANAGER)

        # create test data
        self.create_test_data()

    def test_get_song_list(self):
        """Test to verify song list with no query."""
        # Login as simple user
        self.authenticate(self.user)

        # Get songs list
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)
        self.assertEqual(len(response.data["results"]), 2)

        # Songs are sorted by title
        self.check_song_json(response.data["results"][0], self.song1)
        self.check_song_json(response.data["results"][1], self.song2)

    def test_get_song_long_lyrics(self):
        """Test to get a song with few lyrics."""
        # Login as simple user
        self.authenticate(self.user)

        # add lyrics to one song
        self.song2.lyrics = """Mary had a little lamb
Little lamb, little lamb
Mary had a little lamb
Its fleece was white as snow
And everywhere that Mary went
Mary went, Mary."""
        self.song2.save()

        # Get songs list
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)
        self.assertEqual(len(response.data["results"]), 2)

        # check lyrics
        self.assertDictEqual(
            response.data["results"][1]["lyrics_preview"],
            {
                "text": """Mary had a little lamb
Little lamb, little lamb
Mary had a little lamb
Its fleece was white as snow
And everywhere that Mary went""",
                "truncated": True,
            },
        )

    def test_get_song_list_forbidden(self):
        """Test to verify unauthenticated user can't get songs list."""
        # Attempte to get songs list
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_song_list_with_query(self):
        """Test to verify song list with simple query."""
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

    def test_get_song_list_with_query_empty(self):
        """Test to verify song list with empty query."""
        # Login as simple user
        self.authenticate(self.user)

        # Get songs list with query = ""
        # Should return all songs
        self.song_query_test("", [self.song1, self.song2])

    def test_get_song_list_with_query_detail(self):
        """Test to verify song list with detail query."""
        # Login as simple user
        self.authenticate(self.user)

        # Get songs list with query = "Version2"
        # Should only return song2
        self.song_query_test("ersion2", [self.song2])

        # Get songs list with query = "Detail2"
        # Should only return song2
        self.song_query_test("etail2", [self.song2])

        # Get songs list with query = "Detail_Video2"
        # Should only return song2
        self.song_query_test("etail_Video2", [self.song2])

    def test_get_song_list_with_query_tag(self):
        """Test to verify song list with tag query."""
        # Login as simple user
        self.authenticate(self.user)

        # Get songs list with query = "#TAG1"
        # Should only return song2
        self.song_query_test("#TAG1", [self.song2])

        # Get songs list with query = "#TAG2"
        # Should not return any result
        self.song_query_test("#TAG2", [])

    def test_get_song_list_with_query_artist(self):
        """Test to verify song list with artist query."""
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
        self.song_query_test('artist:""Artist1""', [self.song2])

        # Get songs list with query = "artist:""tist1"""
        # Should not return any result
        self.song_query_test('artist:""tist1""', [])

    def test_get_song_list_with_query_work(self):
        """Test to verify song list with work query."""
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

    def test_get_song_list_with_query_work_alternative_title(self):
        """Test to verify song list with work alternative title query."""
        # Login as simple user
        self.authenticate(self.user)

        # Get songs list with query = "work:AltTitle1"
        # Should only return song2
        self.song_query_test("work:AltTitle1", [self.song2])

        # Get songs list with query = "work:""AltTitle1"""
        # Should only return song2
        self.song_query_test("""work:""AltTitle1"" """, [self.song2])

        # Get songs list with query = "wt1:AltTitle1"
        # Should only return song2
        self.song_query_test("wt1:AltTitle1", [self.song2])

        # Get songs list with query = "wt1:""AltTitle1"""
        # Should only return song2
        self.song_query_test("""wt1:""AltTitle1"" """, [self.song2])

        # Get songs list with query = "AltTitle1"
        # Should only return song2
        self.song_query_test("AltTitle1", [self.song2])

        # Get songs list with query = "wt2:AltTitle1"
        # Should not return any result since Work1 is not of type workType2
        self.song_query_test("wt2:AltTitle1", [])

    def test_get_song_list_with_query_title(self):
        """Test to verify song list with title query."""
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
        """Test to verify song list with title query."""
        # Login as simple user
        self.authenticate(self.user)

        # Get songs list with query = "artist:Artist1 title:1"
        # Should not return any song
        self.song_query_test("artist:Artist1 title:1", [])

    def test_get_song_list_with_query_complex(self):
        """Test to verify parsed query is returned."""
        # Login as simple user
        self.authenticate(self.user)

        query = (
            """hey  artist: me work:you wt1:workName title: test\\ Test """
            """remain stuff #tagg wt3:test artist:"my artist" work:""exact """
            """Work"" i   """
        )

        # Get song list with a complex query
        # should not return any song, but we'll check returned parsed query
        response = self.client.get(self.url, {"query": query})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 0)
        results = response.data["results"]
        self.assertEqual(len(results), 0)
        query = response.data["query"]
        self.assertCountEqual(
            query["remaining"], ["remain", "stuff", "hey", "i", "wt3:test"]
        )
        self.assertCountEqual(query["tag"], ["TAGG"])
        self.assertCountEqual(query["title"]["contains"], ["test Test"])
        self.assertCountEqual(query["title"]["exact"], [])
        self.assertCountEqual(query["artist"]["contains"], ["me", "my artist"])
        self.assertCountEqual(query["artist"]["exact"], [])
        self.assertCountEqual(query["work"]["contains"], ["you"])
        self.assertCountEqual(query["work"]["exact"], ["exact Work"])
        self.assertCountEqual(query["work_type"].keys(), ["wt1"])
        self.assertCountEqual(query["work_type"]["wt1"]["contains"], ["workName"])
        self.assertCountEqual(query["work_type"]["wt1"]["exact"], [])

    def song_query_test(self, query, expected_songs):
        """Method to test a song request with a given query.

        Returned songs should be the same as expected_songs,
        in the same order.
        """
        # TODO This only works when there is only one page of songs
        response = self.client.get(self.url, {"query": query})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], len(expected_songs))
        results = response.data["results"]
        self.assertEqual(len(results), len(expected_songs))
        for song, expected_song in zip(results, expected_songs):
            self.assertEqual(song["id"], expected_song.id)

    def test_get_song_list_disabled_tag(self):
        """Test to verify songs with disabled for user.

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
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(len(response.data["results"]), 1)

        # The remaining song is Song1
        # Song2 has been excluded from the list
        self.check_song_json(response.data["results"][0], self.song1)

    def test_get_song_list_disabled_tag_manager(self):
        """Test to verify songs with disabled tags for manager.

        For a manager, song list includes disabled songs with tags.
        """
        # Login as manager
        self.authenticate(self.manager)

        # Set tag1 disabled
        self.tag1.disabled = True
        self.tag1.save()

        # Get songs list, there should be only one song
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)
        self.assertEqual(len(response.data["results"]), 2)

        # The remaining song is Song1
        # Song2 has been excluded from the list
        self.check_song_json(response.data["results"][0], self.song1)
        self.check_song_json(response.data["results"][1], self.song2)

    def test_post_song_simple(self):
        """Test to create a song without nested artists, tags nor works."""
        # login as manager
        self.authenticate(self.manager)

        # pre assert the amount of songs
        self.assertEqual(Song.objects.count(), 2)

        # create a new song
        song = {
            "title": "Song3",
            "filename": "song3",
            "directory": "directory",
            "duration": 0,
            "lyrics": "mary had a little lamb",
            "version": "version 1",
            "detail": "test",
            "detail_video": "here",
        }
        response = self.client.post(self.url, song)

        # assert the response
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # assert the created song
        song = Song.objects.get(title="Song3")
        self.assertIsNotNone(song)
        self.assertEqual(song.filename, "song3")
        self.assertEqual(song.directory, "directory")
        self.assertEqual(song.duration, timedelta(0))
        self.assertEqual(song.lyrics, "mary had a little lamb")
        self.assertEqual(song.version, "version 1")
        self.assertEqual(song.detail, "test")
        self.assertEqual(song.detail_video, "here")

    def test_post_song_with_tag(self):
        """Test to create a song with nested tags."""
        # login as manager
        self.authenticate(self.manager)

        # pre assert the amount of songs
        self.assertEqual(Song.objects.count(), 2)
        self.assertEqual(SongTag.objects.count(), 2)
        # pre assert
        self.assertNotEqual(self.tag1.color_hue, 256)

        # create a new song
        song = {
            "title": "Song3",
            "filename": "song3",
            "directory": "directory",
            "duration": 0,
            "tags": [
                {"name": "TAG3", "color_hue": 134},
                {"name": self.tag1.name, "color_hue": 256},
            ],
        }
        response = self.client.post(self.url, song)

        # assert the response
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # assert tag3 was created with the given color hue
        self.assertEqual(SongTag.objects.count(), 3)
        tag3 = SongTag.objects.get(name="TAG3")
        self.assertIsNotNone(tag3)
        self.assertEqual(tag3.color_hue, 134)

        # assert tag1 color was not updated
        tag1 = SongTag.objects.get(pk=self.tag1.id)
        self.assertNotEqual(tag1.color_hue, 256)

    def test_post_song_embedded(self):
        """Test to create a song with nested artists, tags and works."""
        # login as manager
        self.authenticate(self.manager)

        # pre assert the amount of songs
        self.assertEqual(Song.objects.count(), 2)
        self.assertEqual(Artist.objects.count(), 2)
        self.assertEqual(SongTag.objects.count(), 2)
        self.assertEqual(Work.objects.count(), 3)

        # create a new song
        song = {
            "title": "Song3",
            "filename": "song3",
            "directory": "directory",
            "duration": 0,
            "artists": [{"name": self.artist1.name}, {"name": "Artist3"}],
            "tags": [{"name": "TAG3"}, {"name": self.tag1.name}],
            "works": [
                {
                    "work": {
                        "title": "Work4",
                        "subtitle": "subtitle4",
                        "work_type": {"query_name": self.wt1.query_name},
                    },
                    "link_type": "OP",
                    "link_type_number": None,
                    "episodes": "",
                },
                {
                    "work": {
                        "title": self.work1.title,
                        "subtitle": self.work1.subtitle,
                        "work_type": {"query_name": self.work1.work_type.query_name},
                    },
                    "link_type": "ED",
                    "link_type_number": 2,
                    "episodes": "1",
                },
            ],
        }
        response = self.client.post(self.url, song)

        # assert the response
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # assert the created song
        song = Song.objects.get(title="Song3")
        self.assertIsNotNone(song)
        self.assertEqual(song.filename, "song3")
        self.assertEqual(song.directory, "directory")
        self.assertEqual(song.duration, timedelta(0))

        # assert the created artists
        self.assertEqual(Artist.objects.count(), 3)
        artist3 = Artist.objects.get(name="Artist3")
        self.assertIsNotNone(artist3)

        self.assertCountEqual(song.artists.all(), [self.artist1, artist3])

        # assert the created tags
        self.assertEqual(SongTag.objects.count(), 3)
        tag3 = SongTag.objects.get(name="TAG3")
        self.assertIsNotNone(tag3)

        self.assertCountEqual(song.tags.all(), [self.tag1, tag3])

        # assert the created works
        self.assertEqual(Work.objects.count(), 4)
        work4 = Work.objects.get(
            title="Work4", subtitle="subtitle4", work_type=self.wt1
        )
        self.assertIsNotNone(work4)

        song_work_link_1 = SongWorkLink.objects.get(song=song, work=self.work1)
        self.assertIsNotNone(song_work_link_1)
        self.assertEqual(song_work_link_1.link_type, SongWorkLink.ENDING)
        self.assertEqual(song_work_link_1.link_type_number, 2)
        self.assertEqual(song_work_link_1.episodes, "1")

        song_work_link_4 = SongWorkLink.objects.get(song=song, work=work4)
        self.assertIsNotNone(song_work_link_4)
        self.assertEqual(song_work_link_4.link_type, SongWorkLink.OPENING)
        self.assertIsNone(song_work_link_4.link_type_number)
        self.assertEqual(song_work_link_4.episodes, "")

        self.assertCountEqual(
            song.songworklink_set.all(), [song_work_link_1, song_work_link_4]
        )

    def test_post_song_embedded_empty(self):
        """Test to create a song with empty keys for artists, tags and works."""
        # login as manager
        self.authenticate(self.manager)

        # pre assert the amount of songs
        self.assertEqual(Song.objects.count(), 2)
        self.assertEqual(Artist.objects.count(), 2)
        self.assertEqual(SongTag.objects.count(), 2)
        self.assertEqual(Work.objects.count(), 3)

        # create a new song
        song = {
            "title": "Song3",
            "filename": "song3",
            "directory": "directory",
            "duration": 0,
            "artists": [],
            "tags": [],
            "works": [],
            "detail": "",
            "lyrics": "",
        }
        response = self.client.post(self.url, song)

        # assert the response
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # assert the created song
        song = Song.objects.get(title="Song3")
        self.assertIsNotNone(song)
        self.assertEqual(song.filename, "song3")
        self.assertEqual(song.directory, "directory")
        self.assertEqual(song.duration, timedelta(0))

        # assert no new artist, tag or work have been created
        self.assertEqual(Artist.objects.count(), 2)
        self.assertEqual(SongTag.objects.count(), 2)
        self.assertEqual(Work.objects.count(), 3)

    def test_post_song_simple_multi(self):
        """Test to create two songs without nested artists, tags nor works."""
        # login as manager
        self.authenticate(self.manager)

        # pre assert the amount of songs
        self.assertEqual(Song.objects.count(), 2)

        # create a new song
        songs = [
            {
                "title": "Song3",
                "filename": "song3",
                "directory": "directory",
                "duration": 0,
                "lyrics": "mary had a little lamb",
                "version": "version 1",
                "detail": "test",
                "detail_video": "here",
            },
            {
                "title": "Song4",
                "filename": "song4",
                "directory": "directory",
                "duration": 0,
                "lyrics": "",
                "version": "",
                "detail": "",
                "detail_video": "",
            },
        ]
        response = self.client.post(self.url, songs)

        # assert the response
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # assert the amount of songs
        self.assertEqual(Song.objects.count(), 4)

        # assert the created songs
        Song.objects.get(title="Song3")
        Song.objects.get(title="Song4")

    def test_post_song_embedded_work_subtitle(self):
        """Test work is created even if similar exists with different subtitle."""
        # Add a subtitle to work1
        self.work1.subtitle = "returns"
        self.work1.save()

        # login as manager
        self.authenticate(self.manager)

        # pre assert the amount of songs
        self.assertEqual(Song.objects.count(), 2)
        self.assertEqual(Artist.objects.count(), 2)
        self.assertEqual(SongTag.objects.count(), 2)
        self.assertEqual(Work.objects.count(), 3)

        # create a new song
        # The works is same title and worktype as existing work, but without subtitle
        # This should create a new work
        song = {
            "title": "Song3",
            "filename": "song3",
            "directory": "directory",
            "duration": 0,
            "artists": [],
            "tags": [],
            "works": [
                {
                    "work": {
                        "title": self.work1.title,
                        "work_type": {"query_name": self.work1.work_type.query_name},
                    },
                    "link_type": "ED",
                    "link_type_number": 2,
                    "episodes": "1",
                }
            ],
        }
        response = self.client.post(self.url, song)

        # assert the response
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # assert the created song
        song = Song.objects.get(title="Song3")
        self.assertIsNotNone(song)
        self.assertEqual(song.filename, "song3")
        self.assertEqual(song.directory, "directory")
        self.assertEqual(song.duration, timedelta(0))

        # assert a new work was created
        self.assertEqual(Work.objects.count(), 4)
        workNew = Work.objects.get(title="Work1", subtitle="", work_type=self.wt1)
        self.assertIsNotNone(workNew)


class SongViewTestCase(LibraryAPITestCase):
    def setUp(self):
        # create a user without any rights
        self.user = self.create_user("TestUser")

        # create a manager
        self.manager = self.create_user("TestManager", library_level=UserModel.MANAGER)

        # create test data
        self.create_test_data()

        # Create urls to access these playlist entries
        self.url_song1 = reverse("library-song", kwargs={"pk": self.song1.id})
        self.url_song2 = reverse("library-song", kwargs={"pk": self.song2.id})

    def test_put_song_simple(self):
        """Test to update a song without nested artists, tags nor works."""
        # login as manager
        self.authenticate(self.manager)

        # create a new song
        song = {
            "title": "Song1 new",
            "filename": "song1 new",
            "directory": "directory new",
            "duration": timedelta(seconds=1),
            "lyrics": "mary had a little lamb",
            "version": "version 1",
            "detail": "test",
            "detail_video": "here",
            "has_instrumental": True,
        }
        response = self.client.put(self.url_song1, song)

        # assert the response
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # assert the created song
        song = Song.objects.get(pk=self.song1.id)
        self.assertEqual(song.title, "Song1 new")
        self.assertEqual(song.filename, "song1 new")
        self.assertEqual(song.directory, "directory new")
        self.assertEqual(song.duration, timedelta(seconds=1))
        self.assertEqual(song.lyrics, "mary had a little lamb")
        self.assertEqual(song.version, "version 1")
        self.assertEqual(song.detail, "test")
        self.assertEqual(song.detail_video, "here")
        self.assertTrue(song.has_instrumental)

    def test_put_song_embedded(self):
        """Test to update a song with nested artists, tags and works."""
        # login as manager
        self.authenticate(self.manager)

        # pre assert the amount of songs
        self.assertEqual(Artist.objects.count(), 2)
        self.assertEqual(SongTag.objects.count(), 2)
        self.assertEqual(Work.objects.count(), 3)

        # create a new song
        song = {
            "title": "Song1 new",
            "filename": "song1 new",
            "directory": "directory new",
            "duration": timedelta(seconds=1),
            "artists": [{"name": self.artist1.name}, {"name": "Artist3"}],
            "tags": [{"name": "TAG3"}, {"name": self.tag1.name}],
            "works": [
                {
                    "work": {
                        "title": "Work4",
                        "subtitle": "subtitle4",
                        "work_type": {"query_name": self.wt1.query_name},
                    },
                    "link_type": "OP",
                    "link_type_number": None,
                    "episodes": "",
                },
                {
                    "work": {
                        "title": self.work1.title,
                        "subtitle": self.work1.subtitle,
                        "work_type": {"query_name": self.work1.work_type.query_name},
                    },
                    "link_type": "ED",
                    "link_type_number": 2,
                    "episodes": "1",
                },
            ],
        }
        response = self.client.put(self.url_song1, song)

        # assert the response
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # assert the created song
        song = Song.objects.get(pk=self.song1.pk)
        self.assertEqual(song.title, "Song1 new")
        self.assertEqual(song.filename, "song1 new")
        self.assertEqual(song.directory, "directory new")
        self.assertEqual(song.duration, timedelta(seconds=1))

        # assert the created artists
        self.assertEqual(Artist.objects.count(), 3)
        artist3 = Artist.objects.get(name="Artist3")
        self.assertIsNotNone(artist3)

        self.assertCountEqual(song.artists.all(), [self.artist1, artist3])

        # assert the created tags
        self.assertEqual(SongTag.objects.count(), 3)
        tag3 = SongTag.objects.get(name="TAG3")
        self.assertIsNotNone(tag3)

        self.assertCountEqual(song.tags.all(), [self.tag1, tag3])

        # assert the created works
        self.assertEqual(Work.objects.count(), 4)
        work4 = Work.objects.get(
            title="Work4", subtitle="subtitle4", work_type=self.wt1
        )
        self.assertIsNotNone(work4)

        song_work_link_1 = SongWorkLink.objects.get(song=song, work=self.work1)
        self.assertIsNotNone(song_work_link_1)
        self.assertEqual(song_work_link_1.link_type, SongWorkLink.ENDING)
        self.assertEqual(song_work_link_1.link_type_number, 2)
        self.assertEqual(song_work_link_1.episodes, "1")

        song_work_link_4 = SongWorkLink.objects.get(song=song, work=work4)
        self.assertIsNotNone(song_work_link_4)
        self.assertEqual(song_work_link_4.link_type, SongWorkLink.OPENING)
        self.assertIsNone(song_work_link_4.link_type_number)
        self.assertEqual(song_work_link_4.episodes, "")

        self.assertCountEqual(
            song.songworklink_set.all(), [song_work_link_1, song_work_link_4]
        )

    def test_put_song_embedded_replace(self):
        """Test to update a song with already defined nested artists, tags and works."""
        # login as manager
        self.authenticate(self.manager)

        # pre assert the amount of songs
        self.assertEqual(Artist.objects.count(), 2)
        self.assertEqual(SongTag.objects.count(), 2)
        self.assertEqual(Work.objects.count(), 3)

        # create a new song
        song = {
            "title": "Song2 new",
            "filename": "song2 new",
            "directory": "directory new",
            "duration": timedelta(seconds=1),
            "artists": [{"name": "Artist3"}],
            "tags": [{"name": "TAG3"}],
            "works": [
                {
                    "work": {
                        "title": "Work4",
                        "subtitle": "subtitle4",
                        "work_type": {"query_name": self.wt1.query_name},
                    },
                    "link_type": "OP",
                    "link_type_number": None,
                    "episodes": "",
                }
            ],
        }
        response = self.client.put(self.url_song2, song)

        # assert the response
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # assert the created song
        song = Song.objects.get(pk=self.song2.pk)
        self.assertEqual(song.title, "Song2 new")
        self.assertEqual(song.filename, "song2 new")
        self.assertEqual(song.directory, "directory new")
        self.assertEqual(song.duration, timedelta(seconds=1))

        # assert the created artists
        self.assertEqual(Artist.objects.count(), 3)
        self.assertEqual(song.artists.count(), 1)
        artist3 = Artist.objects.get(name="Artist3")
        self.assertIsNotNone(artist3)

        self.assertCountEqual(song.artists.all(), [artist3])

        # assert the created tags
        self.assertEqual(SongTag.objects.count(), 3)
        tag3 = SongTag.objects.get(name="TAG3")
        self.assertIsNotNone(tag3)

        self.assertCountEqual(song.tags.all(), [tag3])

        # assert the created works
        self.assertEqual(Work.objects.count(), 4)
        work4 = Work.objects.get(
            title="Work4", subtitle="subtitle4", work_type=self.wt1
        )
        self.assertIsNotNone(work4)

        song_work_link_4 = SongWorkLink.objects.get(song=song, work=work4)
        self.assertIsNotNone(song_work_link_4)
        self.assertEqual(song_work_link_4.link_type, SongWorkLink.OPENING)
        self.assertIsNone(song_work_link_4.link_type_number)
        self.assertEqual(song_work_link_4.episodes, "")

        self.assertCountEqual(song.songworklink_set.all(), [song_work_link_4])

    def test_put_song_embedded_identical(self):
        """Test to update a song with same nested artists, tags and works."""
        # login as manager
        self.authenticate(self.manager)

        # pre assert the amount of songs
        self.assertEqual(Artist.objects.count(), 2)
        self.assertEqual(SongTag.objects.count(), 2)
        self.assertEqual(Work.objects.count(), 3)

        # create a new song
        song = {
            "title": "Song2 new",
            "filename": "song2 new",
            "directory": "directory new",
            "duration": timedelta(seconds=1),
            "artists": [{"name": self.artist1.name}],
            "tags": [{"name": self.tag1.name}],
            "works": [
                {
                    "work": {
                        "title": self.work1.title,
                        "subtitle": self.work1.subtitle,
                        "work_type": {"query_name": self.work1.work_type.query_name},
                    },
                    "link_type": "OP",
                    "link_type_number": None,
                    "episodes": "",
                }
            ],
        }
        response = self.client.put(self.url_song2, song)

        # assert the response
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # assert the created song
        song = Song.objects.get(pk=self.song2.pk)
        self.assertEqual(song.title, "Song2 new")
        self.assertEqual(song.filename, "song2 new")
        self.assertEqual(song.directory, "directory new")
        self.assertEqual(song.duration, timedelta(seconds=1))

        # assert the created artists
        self.assertEqual(Artist.objects.count(), 2)
        self.assertCountEqual(song.artists.all(), [self.artist1])

        # assert the created tags
        self.assertEqual(SongTag.objects.count(), 2)
        self.assertCountEqual(song.tags.all(), [self.tag1])

        # assert the created works
        self.assertEqual(Work.objects.count(), 3)
        song_work_link_1 = SongWorkLink.objects.get(song=song, work=self.work1)
        self.assertIsNotNone(song_work_link_1)
        self.assertEqual(song_work_link_1.link_type, SongWorkLink.OPENING)
        self.assertIsNone(song_work_link_1.link_type_number)
        self.assertEqual(song_work_link_1.episodes, "")
        self.assertCountEqual(song.songworklink_set.all(), [song_work_link_1])

    def test_put_song_embedded_work_subtitle(self):
        """Test work is created even if similar exists with different subtitle."""
        # Add a subtitle to work1
        self.work1.subtitle = "returns"
        self.work1.save()

        # login as manager
        self.authenticate(self.manager)

        # pre assert the amount of songs
        self.assertEqual(Song.objects.count(), 2)
        self.assertEqual(Artist.objects.count(), 2)
        self.assertEqual(SongTag.objects.count(), 2)
        self.assertEqual(Work.objects.count(), 3)

        # update song1
        # The works is same title and worktype as existing work, but without subtitle
        # This should create a new work
        song = {
            "title": "Song1",
            "filename": "file.mp4",
            "directory": "directory",
            "duration": 0,
            "artists": [],
            "tags": [],
            "works": [
                {
                    "work": {
                        "title": self.work1.title,
                        "work_type": {"query_name": self.work1.work_type.query_name},
                    },
                    "link_type": "ED",
                    "link_type_number": 2,
                    "episodes": "1",
                }
            ],
        }
        response = self.client.put(self.url_song1, song)

        # assert the response
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # assert a new work was created
        self.assertEqual(Work.objects.count(), 4)
        workNew = Work.objects.get(title="Work1", subtitle="", work_type=self.wt1)
        self.assertIsNotNone(workNew)
