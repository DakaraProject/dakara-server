import os

from rest_framework import serializers

from library.models import Song, Artist, Work, SongWorkLink, WorkType, SongTag


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
        fields = (
            'id',
            'name',
        )


class ArtistWithCountSerializer(serializers.ModelSerializer):
    """Artist serializer

    Including a song count.
    Used in artists listing.
    """
    song_count = serializers.SerializerMethodField()

    class Meta:
        model = Artist
        fields = (
            'id',
            'name',
            'song_count'
        )

    @staticmethod
    def get_song_count(artist):
        """Count the amount of songs associated to the artist
        """
        return Song.objects.filter(artists=artist).count()


class WorkTypeSerializer(serializers.ModelSerializer):
    """Work type serializer
    """
    class Meta:
        model = WorkType
        fields = (
            'name',
            'name_plural',
            'query_name',
            'icon_name'
        )


class WorkNoCountSerializer(serializers.ModelSerializer):
    """Work serializer
    """
    work_type = WorkTypeSerializer(many=False, read_only=True)

    class Meta:
        model = Work
        fields = (
            'id',
            'title',
            'subtitle',
            'work_type'
        )


class WorkSerializer(serializers.ModelSerializer):
    """Work serializer
    """
    work_type = WorkTypeSerializer(many=False, read_only=True)
    song_count = serializers.SerializerMethodField()

    class Meta:
        model = Work
        fields = (
            'id',
            'title',
            'subtitle',
            'work_type',
            'song_count'
        )

    @staticmethod
    def get_song_count(work):
        """Count the amount of songs associated to the work
        """
        return Song.objects.filter(works=work).count()


class SongWorkLinkSerializer(serializers.ModelSerializer):
    """Serialization of the use of a song in a work
    """
    work = WorkNoCountSerializer(many=False, read_only=True)

    class Meta:
        model = SongWorkLink
        fields = (
            'work',
            'link_type',
            'link_type_number',
            'episodes',
        )


class SongTagSerializer(serializers.ModelSerializer):
    """Song tags serializer
    """
    class Meta:
        model = SongTag
        fields = (
            'id',
            'name',
            'color_hue',
            'disabled',
        )


class SongSerializer(serializers.ModelSerializer):
    """Song serializer
    """
    duration = SecondsDurationField()
    artists = ArtistSerializer(many=True, read_only=True)
    tags = SongTagSerializer(many=True, read_only=True)
    works = SongWorkLinkSerializer(many=True, read_only=True,
                                   source='songworklink_set')
    lyrics = serializers.SerializerMethodField()

    class Meta:
        model = Song
        fields = (
            'id',
            'title',
            'filename',
            'directory',
            'duration',
            'version',
            'detail',
            'detail_video',
            'tags',
            'artists',
            'works',
            'lyrics',
            'date_created',
            'date_updated',
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
            return {'text': song.lyrics}

        return {
            'text': '\n'.join(lyrics_list[:max_lines]),
            'truncated': True
        }


class SongForPlayerSerializer(serializers.ModelSerializer):
    """Song serializer

    To be used by the player.
    """
    artists = ArtistSerializer(many=True, read_only=True)
    works = SongWorkLinkSerializer(
        many=True,
        read_only=True,
        source='songworklink_set')
    file_path = serializers.SerializerMethodField()

    class Meta:
        model = Song
        fields = (
            'title',
            'artists',
            'works',
            'file_path',
        )

    @staticmethod
    def get_file_path(song):
        """Add directory to song file name
        """
        return os.path.join(song.directory, song.filename)
