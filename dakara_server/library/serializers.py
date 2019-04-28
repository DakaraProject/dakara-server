import os

from rest_framework import serializers

from library.models import (
    Song,
    Artist,
    Work,
    SongWorkLink,
    WorkType,
    SongTag,
    WorkAlternativeTitle,
)


class SecondsDurationField(serializers.DurationField):
    """Field that displays only seconds
    """

    def to_representation(self, value):
        """Method for serializing duration in right format
        """
        return int(round(value.total_seconds()))


class ArtistSerializer(serializers.ModelSerializer):
    """Artist serializer

    Used in song representation.
    """

    class Meta:
        model = Artist
        fields = ("id", "name")


class ArtistWithCountSerializer(serializers.ModelSerializer):
    """Artist serializer

    Including a song count.
    Used in artists listing.
    """

    song_count = serializers.SerializerMethodField()

    class Meta:
        model = Artist
        fields = ("id", "name", "song_count")

    @staticmethod
    def get_song_count(artist):
        """Count the amount of songs associated to the artist
        """
        return Song.objects.filter(artists=artist).count()


class WorkAlternativeTitleSerializer(serializers.ModelSerializer):
    """Work alternative title serialize
    """

    class Meta:
        model = WorkAlternativeTitle
        fields = ("title",)


class WorkTypeSerializer(serializers.ModelSerializer):
    """Work type serializer
    """

    class Meta:
        model = WorkType
        fields = ("name", "name_plural", "query_name", "icon_name")
        extra_kwargs = {
            "name": {"required": False},
            "name_plural": {"required": False},
            "icon_name": {"required": False},
            "query_name": {"validators": []},
        }


class WorkNoCountSerializer(serializers.ModelSerializer):
    """Work serializer
    """

    alternative_titles = WorkAlternativeTitleSerializer(many=True, read_only=True)
    work_type = WorkTypeSerializer(many=False)

    class Meta:
        model = Work
        fields = ("id", "title", "subtitle", "alternative_titles", "work_type")


class WorkSerializer(serializers.ModelSerializer):
    """Work serializer
    """

    alternative_titles = WorkAlternativeTitleSerializer(many=True, read_only=True)
    work_type = WorkTypeSerializer(many=False, read_only=True)
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

    @staticmethod
    def get_song_count(work):
        """Count the amount of songs associated to the work
        """
        return Song.objects.filter(works=work).count()


class SongWorkLinkSerializer(serializers.ModelSerializer):
    """Serialization of the use of a song in a work
    """

    work = WorkNoCountSerializer(many=False)

    class Meta:
        model = SongWorkLink
        fields = ("work", "link_type", "link_type_number", "episodes")


class SongTagSerializer(serializers.ModelSerializer):
    """Song tags serializer
    """

    class Meta:
        model = SongTag
        fields = ("id", "name", "color_hue", "disabled")


class SongSerializer(serializers.ModelSerializer):
    """Song serializer
    """

    duration = SecondsDurationField()
    artists = ArtistSerializer(many=True, required=False)
    tags = SongTagSerializer(many=True, required=False)
    works = SongWorkLinkSerializer(many=True, source="songworklink_set", required=False)
    lyrics = serializers.SerializerMethodField()

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
            "date_created",
            "date_updated",
        )

    @staticmethod
    def get_lyrics(song, max_lines=5):
        """Get an extract of the lyrics

        Give at most `max_lines` lines of lyrics and tell if more lines remain.
        """
        if not song.lyrics:
            return None

        lyrics_list = song.lyrics.splitlines()

        if len(lyrics_list) <= max_lines:
            return {"text": song.lyrics}

        return {"text": "\n".join(lyrics_list[:max_lines]), "truncated": True}

    def create(self, validated_data):
        """Create the Song instance
        """
        # create vanilla song
        artists_data = validated_data.pop("artists", [])
        tags_data = validated_data.pop("tags", [])
        songworklinks_data = validated_data.pop("songworklink_set", [])
        song = Song.objects.create(**validated_data)

        # create artists and add them
        for artist_data in artists_data:
            artist, _ = Artist.objects.get_or_create(**artist_data)
            song.artists.add(artist)

        # create tags and add them
        for tag_data in tags_data:
            tag, _ = SongTag.objects.get_or_create(**tag_data)
            song.tags.add(tag)

        # create works and add them
        for songworklink_data in songworklinks_data:
            work_data = songworklink_data.pop("work")
            work_type_data = work_data.pop("work_type")

            # create work type
            work_type, _ = WorkType.objects.get_or_create(
                query_name=work_type_data["query_name"],
                # TODO add defaults
            )

            # create work
            work, _ = Work.objects.get_or_create(**work_data, work_type=work_type)

            # create work link
            SongWorkLink.objects.create(**songworklink_data, song=song, work=work)

        return song

    def update(self, song, validated_data):
        """Update the Song instance
        """
        # create vanilla song
        artists_data = validated_data.pop("artists", [])
        tags_data = validated_data.pop("tags", [])
        songworklinks_data = validated_data.pop("songworklink_set", [])
        song = super().update(song, validated_data)

        # create artists and add them
        artists = [
            Artist.objects.get_or_create(**artist_data)[0]
            for artist_data in artists_data
        ]
        song.artists.set(artists)

        # create tags and add them
        tags = [SongTag.objects.get_or_create(**tag_data)[0] for tag_data in tags_data]
        song.tags.set(tags)

        # create works and add them
        songworklinks_old = set(song.songworklink_set.all())
        for songworklink_data in songworklinks_data:
            work_data = songworklink_data.pop("work")
            work_type_data = work_data.pop("work_type")

            # create work type
            work_type, _ = WorkType.objects.get_or_create(
                query_name=work_type_data["query_name"],
                # TODO add defaults
            )

            # create work
            work, work_created = Work.objects.get_or_create(
                **work_data, work_type=work_type
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

        return song


class SongForPlayerSerializer(serializers.ModelSerializer):
    """Song serializer

    To be used by the player.
    """

    artists = ArtistSerializer(many=True, read_only=True)
    works = SongWorkLinkSerializer(many=True, read_only=True, source="songworklink_set")
    file_path = serializers.SerializerMethodField()

    class Meta:
        model = Song
        fields = ("title", "artists", "works", "file_path")

    @staticmethod
    def get_file_path(song):
        """Add directory to song file name
        """
        return os.path.join(song.directory, song.filename)


class SongForFeederSerializer(serializers.ModelSerializer):
    """Song serializer for the feeder
    """

    class Meta:
        model = Song
        fields = ("filename", "directory")
