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


class WorkTypeSerializer(serializers.ModelSerializer):
    """Work type serializer."""

    class Meta:
        model = WorkType
        fields = ("name", "name_plural", "query_name", "icon_name")


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


class WorkNoCountSerializer(serializers.ModelSerializer):
    """Work serializer."""

    alternative_titles = WorkAlternativeTitleSerializer(many=True, read_only=True)
    work_type = WorkTypeForWorkSerializer(many=False)

    class Meta:
        model = Work
        fields = ("id", "title", "subtitle", "alternative_titles", "work_type")


class WorkSerializer(serializers.ModelSerializer):
    """Work serializer."""

    alternative_titles = WorkAlternativeTitleSerializer(many=True)
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
        read_only_fiels = ("id", "song_count")

    @staticmethod
    def get_song_count(work):
        """Count the amount of songs associated to the work."""
        return Song.objects.filter(works=work).count()

    def create(self, validated_data):
        """Create the Work instance."""
        alternative_titles_data = validated_data.pop("alternative_titles", [])
        work_type_data = validated_data.pop("work_type")

        work_type = self.set_work_type(work_type_data)
        work = super().create({**validated_data, "work_type": work_type})

        self.set_alternative_titles(work, alternative_titles_data)

        return work

    def update(self, work, validated_data):
        """Create the Work instance."""
        alternative_titles_data = validated_data.pop("alternative_titles", [])
        work_type_data = validated_data.pop("work_type")

        work_type = self.set_work_type(work_type_data)
        work = super().update(work, {**validated_data, "work_type": work_type})

        self.set_alternative_titles(work, alternative_titles_data)

        return work

    @staticmethod
    def set_alternative_titles(work, alternative_titles_data):
        alternative_titles = [
            WorkAlternativeTitle.objects.get_or_create(
                **alternative_title_data, work=work
            )[0]
            for alternative_title_data in alternative_titles_data
        ]
        work.alternative_titles.set(alternative_titles)

    @staticmethod
    def set_work_type(work_type_data):
        # create work type
        # if only query name is provided and work type does not exist,
        # populate other name fields with query name
        query_name = work_type_data["query_name"]
        work_type, _ = WorkType.objects.get_or_create(
            query_name=query_name,
            defaults={
                "query_name": query_name,
                "name": work_type_data.get("name", query_name),
                "name_plural": work_type_data.get("name_plural", query_name),
            },
        )

        return work_type


class SongWorkLinkSerializer(serializers.ModelSerializer):
    """Serialization of the use of a song in a work."""

    work = WorkNoCountSerializer(many=False)

    class Meta:
        model = SongWorkLink
        fields = ("work", "link_type", "link_type_number", "episodes")


class SongTagSerializer(serializers.ModelSerializer):
    """Song tags serializer."""

    class Meta:
        model = SongTag
        fields = ("id", "name", "color_hue", "disabled")


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

        self.set_artists(song, artists_data)
        self.set_tags(song, tags_data)
        self.set_songworklinks(song, songworklinks_data)

        return song

    def update(self, song, validated_data):
        """Update the Song instance."""
        # create vanilla song
        artists_data = validated_data.pop("artists", [])
        tags_data = validated_data.pop("tags", [])
        songworklinks_data = validated_data.pop("songworklink_set", [])
        song = super().update(song, validated_data)
        songworklinks_old = set(song.songworklink_set.all())

        self.set_artists(song, artists_data)
        self.set_tags(song, tags_data)
        self.set_songworklinks(song, songworklinks_data, songworklinks_old)

        return song

    @staticmethod
    def set_artists(song, artists_data):
        """Create artists and add them.

        Args:
            artists_data (list): List of new artists data.
        """
        artists = [
            Artist.objects.get_or_create(**artist_data)[0]
            for artist_data in artists_data
        ]
        song.artists.set(artists)

    @staticmethod
    def set_tags(song, tags_data):
        """Create tags and add them.

        Get the tag with its name only, or create it with all its attributes.

        Args:
            tags_data (list): List of new song tags data.
        """
        tags = [
            SongTag.objects.get_or_create(name=tag_data["name"], defaults=tag_data)[0]
            for tag_data in tags_data
        ]
        song.tags.set(tags)

    @staticmethod
    def set_songworklinks(song, songworklinks_data, songworklinks_old=[]):
        """Create works and add them.

        Args:
            songworklinks_data (list): List of new work links data.
            songworklinks_old (list): List of current work lings.
        """
        for songworklink_data in songworklinks_data:
            work_data = songworklink_data.pop("work")
            work_type_data = work_data.pop("work_type")

            # create work type
            # if only query name is provided and work type does not exist,
            # populate other name fields with query name
            query_name = work_type_data["query_name"]
            work_type, _ = WorkType.objects.get_or_create(
                query_name=query_name,
                defaults={
                    "query_name": query_name,
                    "name": work_type_data.get("name", query_name),
                    "name_plural": work_type_data.get("name_plural", query_name),
                },
            )

            # create work
            work, work_created = Work.objects.get_or_create(
                title=work_data["title"],
                subtitle=work_data.get("subtitle", ""),
                work_type=work_type,
            )
            songworklink = SongWorkLink(**songworklink_data, song=song, work=work)

            # the link already exists
            if not work_created and songworklink in songworklinks_old:
                songworklinks_old.remove(songworklink)

            # otherwise create work link
            else:
                songworklink.save()

        # remove removed links
        for songworklink_old in songworklinks_old:
            songworklink_old.delete()


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


class SongOnlyFilePathSerializer(serializers.ModelSerializer):
    """Song serializer for the feeder."""

    class Meta:
        model = Song
        fields = ("id", "filename", "directory")
