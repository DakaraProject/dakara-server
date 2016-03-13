from rest_framework import serializers
from library.models import Song


class SecondsDurationField(serializers.DurationField):
    """ Field that displays only seconds
    """

    def to_representation(self, obj):
        """ Method for serializing duration in right format
        """
        return str(int(round(obj.total_seconds())))


class SongSerializer(serializers.HyperlinkedModelSerializer):
    """ Class for song serializer
    """
    duration = SecondsDurationField()

    class Meta:
        model = Song
        fields = (
                'id',
                'url',
                'title',
                'file_path',
                'duration',
                'date_created',
                'date_updated',
                )


class SongForPlayerSerializer(serializers.ModelSerializer):
    """ Class for song serializer
    """
    class Meta:
        model = Song
        fields = (
                'title',
                'file_path',
                )
