from rest_framework import serializers
from library.models import Song


class MinutesSecondsDurationField(serializers.DurationField):
    """ Field that displays only minues and seconds
    """

    def to_representation(self, obj):
        """ Method for serializing duration in right format
        """
        seconds = int(obj.total_seconds())
        minutes = seconds // 60
        seconds = seconds % 60
        return "{m:02n}:{s:02n}".format(
                m=minutes,
                s=seconds
                )


class SongSerializer(serializers.HyperlinkedModelSerializer):
    """ Class for song serializer
    """
    duration = MinutesSecondsDurationField()

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
