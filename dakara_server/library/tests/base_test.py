from internal.tests.base_test import BaseProvider, BaseAPITestCase
from library.models import (
    WorkType,
    Work,
    Artist,
    SongTag,
    Song,
    SongWorkLink,
    WorkAlternativeTitle,
)


class LibraryProvider(BaseProvider):
    """Provides helper functions for library tests
    """

    def create_test_data(self):
        """Populate the library with dummy data
        """
        # Create work types
        self.wt1 = WorkType(
            name="WorkType1", name_plural="WorkTypes1", query_name="wt1"
        )
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

        # Create work titles
        WorkAlternativeTitle(title="AltTitle1", work=self.work1).save()
        WorkAlternativeTitle(title="AltTitle2", work=self.work1).save()
        WorkAlternativeTitle(title="AltTitle2", work=self.work2).save()

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
        self.song1 = Song(title="Song1", filename="file.mp4", directory="directory")

        self.song1.save()

        # Song associated with work, artist, tag and details
        self.song2 = Song(
            title="Song2",
            filename="file.mp4",
            version="Version2",
            detail="Detail2",
            detail_video="Detail_Video2",
            has_instrumental=True,
        )
        self.song2.save()
        self.song2.tags.add(self.tag1)
        self.song2.artists.add(self.artist1)
        SongWorkLink(
            song_id=self.song2.id, work_id=self.work1.id, link_type=SongWorkLink.OPENING
        ).save()

    def check_song_json(self, json, expected_song):
        """Method to test a song representation against the expected song
        """
        self.assertEqual(json["id"], expected_song.id)
        self.assertEqual(json["title"], expected_song.title)
        self.assertEqual(json["filename"], expected_song.filename)
        self.assertEqual(json["directory"], expected_song.directory)
        self.assertEqual(json["version"], expected_song.version)
        self.assertEqual(json["detail"], expected_song.detail)
        self.assertEqual(json["detail_video"], expected_song.detail_video)
        self.assertEqual(json["has_instrumental"], expected_song.has_instrumental)

        # tags
        expected_tags = expected_song.tags.all()
        self.assertEqual(len(json["tags"]), len(expected_tags))
        for tag, expected_tag in zip(json["tags"], expected_tags):
            self.check_tag_json(tag, expected_tag)

        # artists
        expected_artists = expected_song.artists.all()
        self.assertEqual(len(json["artists"]), len(expected_artists))
        for artist, expected_artist in zip(json["artists"], expected_artists):
            self.check_artist_json(artist, expected_artist)

        # works
        expected_works = expected_song.songworklink_set.all()
        self.assertEqual(len(json["works"]), len(expected_works))
        for work, expected_work in zip(json["works"], expected_works):
            self.check_work_json(work["work"], expected_work.work)
            self.assertEqual(work["link_type"], expected_work.link_type)
            self.assertEqual(work["link_type_number"], expected_work.link_type_number)
            self.assertEqual(work["episodes"], expected_work.episodes)

    def check_tag_json(self, json, expected_tag):
        """Method to test an representation against the expected tag
        """
        self.assertEqual(json["id"], expected_tag.id)
        self.assertEqual(json["name"], expected_tag.name)
        self.assertEqual(json["color_hue"], expected_tag.color_hue)
        self.assertEqual(json["disabled"], expected_tag.disabled)

    def check_artist_json(self, json, expected_artist):
        """Method to test an representation against the expected artist
        """
        self.assertEqual(json["id"], expected_artist.id)
        self.assertEqual(json["name"], expected_artist.name)

    def check_work_json(self, json, expected_work):
        """Method to test an representation against the expected work
        """
        self.assertEqual(json["id"], expected_work.id)
        self.assertEqual(json["title"], expected_work.title)
        self.assertEqual(json["subtitle"], expected_work.subtitle)
        self.check_work_type_json(json["work_type"], expected_work.work_type)
        # alternative titles
        expected_alt_titles = expected_work.alternative_titles.all()
        self.assertEqual(len(json["alternative_titles"]), len(expected_alt_titles))
        for alt_title, expected_alt_title in zip(
            json["alternative_titles"], expected_alt_titles
        ):
            self.assertEqual(alt_title["title"], expected_alt_title.title)

    def check_work_type_json(self, json, expected_work_type):
        """Method to test an representation against the expected work type
        """
        self.assertEqual(json["name"], expected_work_type.name)
        self.assertEqual(json["name_plural"], expected_work_type.name_plural)
        self.assertEqual(json["query_name"], expected_work_type.query_name)
        self.assertEqual(json["icon_name"], expected_work_type.icon_name)


class LibraryAPITestCase(BaseAPITestCase, LibraryProvider):
    """Base library test class for Unittest
    """
