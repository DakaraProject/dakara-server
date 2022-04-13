import os

from rest_framework import serializers

from library.models import (
    Artist,
    Song,
    SongTag,
    SongWorkLink,
    Work,
    WorkAlternativeTitle,
    WorkType,
)


class SecondsDurationField(serializers.DurationField):
    """Field that displays only seconds."""

    def to_representation(self, value):
        """Method for serializing duration in right format."""
        return int(round(value.total_seconds()))


class ArtistSerializer(serializers.ModelSerializer):
    """Artist serializer.

    Used in song representation.
    """

    class Meta:
        model = Artist
        fields = ("id", "name")

    @staticmethod
    def set(song, artists_data):
        """Create artists for a song.

        Existing associated artists will be cleaned, but not deleted.

        Args:
            song (models.Song): Song to associate artists to.
            artists_data (list): List of new artists data.

        Returns:
            list of models.Artist: List of artists.
        """
        artists = [
            Artist.objects.get_or_create(**artist_data)[0]
            for artist_data in artists_data
        ]
        song.artists.set(artists)

        return artists


class ArtistWithCountSerializer(serializers.ModelSerializer):
    """Artist serializer.

    Including a song count.
    Used in artists listing.
    """

    song_count = serializers.SerializerMethodField()

    class Meta:
        model = Artist
        fields = ("id", "name", "song_count")

    @staticmethod
    def get_song_count(artist):
        """Count the amount of songs associated to the artist."""
        return Song.objects.filter(artists=artist).count()


class WorkAlternativeTitleSerializer(serializers.ModelSerializer):
    """Work alternative title serialize."""

    class Meta:
        model = WorkAlternativeTitle
        fields = ("title",)

    @staticmethod
    def set(work, alternative_titles_data):
        """Create alternative titles for a work.

        Existing associated alternative titles will be deleted if they are not
        set again.

        Args:
            work (models.WorkAlternativeTitle): Work to associate alternative
                titles to.
            alternative_titles_data (list): List of new alternative title data.

        Returns:
            list of models.WorkAlternativeTitle: List of alternative titles.
        """
        alternative_titles_old = work.alternative_titles.all()
        alternative_titles = [
            WorkAlternativeTitle.objects.get_or_create(
                **alternative_title_data, work=work
            )[0]
            for alternative_title_data in alternative_titles_data
        ]

        # clean previous alternative titles that are no longer associated
        for alternative_title_old in alternative_titles_old:
            if alternative_title_old not in alternative_titles:
                alternative_title_old.delete()

        return alternative_titles


class WorkTypeSerializer(serializers.ModelSerializer):
    """Work type serializer."""

    class Meta:
        model = WorkType
        fields = ("name", "name_plural", "query_name", "icon_name")

    @staticmethod
    def set(work_type_data):
        """Create a work type.

        If only query name is provided and work type does not exist, populate
        other name fields with query name.

        Args:
            work_type_data (dict): Data to create a new work type.

        Returns:
            models.WorkType: Work type.
        """
        query_name = work_type_data["query_name"]
        work_type, _ = WorkType.objects.get_or_create(
            query_name=query_name,
            defaults=work_type_data,
        )

        return work_type


class WorkTypeForWorkSerializer(serializers.ModelSerializer):
    """Work type serializer for song."""

    class Meta:
        model = WorkType
        fields = ("name", "name_plural", "query_name", "icon_name")
        extra_kwargs = {
            "name": {"required": False},
            "name_plural": {"required": False},
            "query_name": {"validators": []},
        }


class WorkTypeOnlyQueryNameSerializer(serializers.ModelSerializer):
    """Work type serializer containing the query name only."""

    class Meta:
        model = WorkType
        fields = ("query_name",)


class WorkNoCountSerializer(serializers.ModelSerializer):
    """Work serializer."""

    alternative_titles = WorkAlternativeTitleSerializer(many=True, read_only=True)
    work_type = WorkTypeForWorkSerializer(many=False)

    class Meta:
        model = Work
        fields = ("id", "title", "subtitle", "alternative_titles", "work_type")


class WorkSerializer(serializers.ModelSerializer):
    """Work serializer."""

    alternative_titles = WorkAlternativeTitleSerializer(many=True, required=False)
    work_type = WorkTypeForWorkSerializer(many=False)
    song_count = serializers.SerializerMethodField()

    class Meta:
        model = Work
        fields = (
            "id",
            "title",
            "subtitle",
            "alternative_titles",
            "work_type",
            "song_count",
        )
        read_only_fields = ("id", "song_count")

    @staticmethod
    def get_song_count(work):
        """Count the amount of songs associated to the work.

        Args:
            work (models.Work): Work to count songs of.

        Returns:
            int: Number of songs associated with the provided work.
        """
        return Song.objects.filter(works=work).count()

    def create(self, validated_data):
        """Create the Work instance."""
        alternative_titles_data = validated_data.pop("alternative_titles", [])
        work_type_data = validated_data.pop("work_type")

        work_type = WorkTypeSerializer.set(work_type_data)
        work = super().create({**validated_data, "work_type": work_type})

        WorkAlternativeTitleSerializer.set(work, alternative_titles_data)

        return work

    def update(self, work, validated_data):
        """Create the Work instance."""
        alternative_titles_data = validated_data.pop("alternative_titles", [])
        work_type_data = validated_data.pop("work_type")

        work_type = WorkTypeSerializer.set(work_type_data)
        work = super().update(work, {**validated_data, "work_type": work_type})

        WorkAlternativeTitleSerializer.set(work, alternative_titles_data)

        return work

    @staticmethod
    def set(work_type, work_data):
        """Create work of desired work type.

        Args:
            work_type (models.WorkType): Type of the work.
            work_data (dict): Data to create a new work.

        Returns:
            models.Work: Work.
        """
        # set subtitle to empty string by default
        work_data["subtitle"] = work_data.get("subtitle", "")

        work, _ = Work.objects.get_or_create(
            **work_data,
            work_type=work_type,
        )
        return work


class SongWorkLinkSerializer(serializers.ModelSerializer):
    """Serialization of the use of a song in a work."""

    work = WorkNoCountSerializer(many=False)

    class Meta:
        model = SongWorkLink
        fields = ("work", "link_type", "link_type_number", "episodes")

    @staticmethod
    def set(song, songworklinks_data):
        """Create work links for a song.

        Existing associated song work links will be deleted inconditionnaly.

        Args:
            song (models.Song): Song to associate artists to.
            songworklinks_data (list): List of new work links data.

        Returns:
            list of models.SongWorkLink: List of song-work links.
        """
        # remove all existing song-work links for this song
        song.songworklink_set.all().delete()

        songworklinks = []
        for songworklink_data in songworklinks_data:
            work_data = songworklink_data.pop("work")
            work_type_data = work_data.pop("work_type")

            work_type = WorkTypeSerializer.set(work_type_data)
            work = WorkSerializer.set(work_type, work_data)

            songworklink = SongWorkLink.objects.create(
                **songworklink_data, song=song, work=work
            )
            songworklinks.append(songworklink)

        return songworklinks


class SongTagSerializer(serializers.ModelSerializer):
    """Song tags serializer."""

    class Meta:
        model = SongTag
        fields = ("id", "name", "color_hue", "disabled")

    @staticmethod
    def set(song, tags_data):
        """Create tags for a song.

        Get the tag with its name only, or create it with all its attributes.
        Existing associated song tags will be cleaned, but not deleted.

        Args:
            song (models.Song): Song to associate artists to.
            tags_data (list): List of new song tags data.

        Returns:
            list of models.SongTag: List of song tags.
        """
        tags = [
            SongTag.objects.get_or_create(name=tag_data["name"], defaults=tag_data)[0]
            for tag_data in tags_data
        ]
        song.tags.set(tags)

        return tags


class SongTagForSongSerializer(serializers.ModelSerializer):
    """Song tags for song serializer."""

    class Meta:
        model = SongTag
        fields = ("id", "name", "color_hue", "disabled")
        extra_kwargs = {"name": {"validators": []}}


class SongSerializer(serializers.ModelSerializer):
    """Song serializer."""

    duration = SecondsDurationField()
    artists = ArtistSerializer(many=True, required=False)
    tags = SongTagForSongSerializer(many=True, required=False)
    works = SongWorkLinkSerializer(many=True, source="songworklink_set", required=False)
    lyrics_preview = serializers.SerializerMethodField()

    class Meta:
        model = Song
        fields = (
            "id",
            "title",
            "filename",
            "directory",
            "duration",
            "version",
            "detail",
            "detail_video",
            "tags",
            "artists",
            "works",
            "lyrics",
            "lyrics_preview",
            "has_instrumental",
            "date_created",
            "date_updated",
        )
        extra_kwargs = {"lyrics": {"write_only": True}}

    @staticmethod
    def get_lyrics_preview(song, max_lines=5):
        """Get an extract of the lyrics.

        Give at most `max_lines` lines of lyrics and tell if more lines remain.
        """
        if not song.lyrics:
            return None

        lyrics_list = song.lyrics.splitlines()

        if len(lyrics_list) <= max_lines:
            return {"text": song.lyrics}

        return {"text": "\n".join(lyrics_list[:max_lines]), "truncated": True}

    def create(self, validated_data):
        """Create the Song instance."""
        # create vanilla song
        artists_data = validated_data.pop("artists", [])
        tags_data = validated_data.pop("tags", [])
        songworklinks_data = validated_data.pop("songworklink_set", [])
        song = super().create(validated_data)

        ArtistSerializer.set(song, artists_data)
        SongTagSerializer.set(song, tags_data)
        SongWorkLinkSerializer.set(song, songworklinks_data)

        return song

    def update(self, song, validated_data):
        """Update the Song instance."""
        # create vanilla song
        artists_data = validated_data.pop("artists", [])
        tags_data = validated_data.pop("tags", [])
        songworklinks_data = validated_data.pop("songworklink_set", [])
        song = super().update(song, validated_data)

        ArtistSerializer.set(song, artists_data)
        SongTagSerializer.set(song, tags_data)
        SongWorkLinkSerializer.set(song, songworklinks_data)

        return song


class SongForPlayerSerializer(serializers.ModelSerializer):
    """Song serializer.

    To be used by the player.
    """

    artists = ArtistSerializer(many=True, read_only=True)
    works = SongWorkLinkSerializer(many=True, read_only=True, source="songworklink_set")
    file_path = serializers.SerializerMethodField()

    class Meta:
        model = Song
        fields = ("title", "artists", "works", "file_path", "has_instrumental")

    @staticmethod
    def get_file_path(song):
        """Add directory to song file name."""
        return os.path.join(song.directory, song.filename)


class SongForFeederSerializer(serializers.ModelSerializer):
    """Song serializer for the feeder."""

    class Meta:
        model = Song
        fields = ("id", "filename", "directory")
        read_only_fields = ("id", "filename", "directory")


class SongForDigestSerializer(serializers.ModelSerializer):
    """Song serializer for playlist digest info."""

    class Meta:
        model = Song
        fields = ("id", "title")
        read_only_fields = ("id", "title")


class WorkForFeederSerializer(serializers.ModelSerializer):
    """Work serializer for the feeder."""

    work_type = WorkTypeOnlyQueryNameSerializer(many=False)

    class Meta:
        model = Work
        fields = ("id", "title", "subtitle", "work_type")
        read_only_fields = ("id", "title", "subtitle", "work_type")
