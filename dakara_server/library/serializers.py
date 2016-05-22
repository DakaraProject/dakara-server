from rest_framework import serializers
from library.models import Song, Artist, Work, SongWorkLink, WorkType, SongTag


class SecondsDurationField(serializers.DurationField):
    """ Field that displays only seconds
    """

    def to_representation(self, obj):
        """ Method for serializing duration in right format
        """
        return str(int(round(obj.total_seconds())))


class ArtistSerializer(serializers.ModelSerializer):
    """ Class for artist serializer
    """
    class Meta:
        model = Artist
        fields = (
                'name',
                )


class WorkTypeSerializer(serializers.ModelSerializer):
    """ Class for work type serializer
    """
    class Meta:
        model = WorkType 
        fields = (
                'name',
                'icon_name'
                )


class WorkSerializer(serializers.ModelSerializer):
    """ Class for work serializer
    """
    work_type = WorkTypeSerializer(many=False, read_only=True)
    class Meta:
        model = Work
        fields = (
                'title',
                'subtitle',
                'work_type'
                )


class SongWorkLinkSerializer(serializers.ModelSerializer):
    """ Class for serializing the use of a song in a work
    """
    work = WorkSerializer(many=False, read_only=True)

    class Meta:
        model = SongWorkLink
        fields = (
                'work',
                'link_type',
                'link_type_number',
                )


class SongTagSerializer(serializers.ModelSerializer):
    """ Class for song tags serializer
    """
    class Meta:
        model = SongTag
        fields = (
                'name',
                'color_id',
                )


class SongSerializer(serializers.HyperlinkedModelSerializer):
    """ Class for song serializer
    """
    duration = SecondsDurationField()
    artists = ArtistSerializer(many=True, read_only=True)
    tags = SongTagSerializer(many=True, read_only=True)
    works = SongWorkLinkSerializer(many=True, read_only=True, source='songworklink_set')

    class Meta:
        model = Song
        fields = (
                'id',
                'url',
                'title',
                'file_path',
                'duration',
                'detail',
                'tags',
                'artists',
                'works',
                'date_created',
                'date_updated',
                )


class SongForPlayerSerializer(serializers.ModelSerializer):
    """ Class for song serializer, to be used by the player
    """
    class Meta:
        model = Song
        fields = (
                'title',
                'file_path',
                )
