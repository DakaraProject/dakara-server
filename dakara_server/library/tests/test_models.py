from datetime import timedelta

import pytest

from library import models


class TestStringification:
    """Test the string methods
    """

    def test_song_str(self):
        """Test the string representation of a song
        """
        song = models.Song(
            title="Zankoku na tenshi no teze",
            filename="zankoku_na_tenshi_no_teze.mkv",
            directory="anime",
            duration=timedelta(seconds=90),
        )

        assert str(song) == "Zankoku na tenshi no teze"

    def test_artist_str(self):
        """Test the string representation of an artist
        """
        artist = models.Artist(name="Hatsune Miku")

        assert str(artist) == "Hatsune Miku"

    @pytest.mark.django_db
    def test_work_str(self, library_provider):
        """Test the string representation of a work
        """
        work1 = models.Work(
            title="Evangelion",
            subtitle="The series that drive you nuts",
            work_type=library_provider.wt1,
        )

        assert str(work1) == "Evangelion (WorkType1)"

    @pytest.mark.django_db
    def test_work_alternative_title_str(self, library_provider):
        """Test the string representation of a work alternative title
        """
        name = models.WorkAlternativeTitle(
            title="Uevangelion", work=library_provider.work1
        )

        assert str(name) == "Uevangelion [Work1 (WorkType1)]"

    def test_work_type_str(self):
        """Test the string representation of a work type
        """
        work_type1 = models.WorkType(
            name="Anime", name_plural="Animes", query_name="anime", icon_name="tv"
        )

        assert str(work_type1) == "Anime"

        work_type2 = models.WorkType(query_name="jpop")

        assert str(work_type2) == "jpop"

    @pytest.mark.django_db
    def test_song_work_link_str(self, library_provider):
        """Test the string representation of a song work link
        """
        work_link = models.SongWorkLink(
            song=library_provider.song1,
            work=library_provider.work1,
            link_type=models.SongWorkLink.OPENING,
            link_type_number=2,
        )

        assert str(work_link) == "Song1 <OP> Work1 (WorkType1)"

    def test_song_tag_str(self):
        """Test the string representation of a tag
        """
        tag = models.SongTag(name="Rock and roll", color_hue=180, disabled=True)

        assert str(tag) == "Rock and roll"
