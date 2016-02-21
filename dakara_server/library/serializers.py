from rest_framework import serializers
from library.models import *


class SongSerializer(serializers.HyperlinkedModelSerializer):
    """ Class for song serializer
    """
    class Meta:
        model = Song
        fields = (
                'id',
                'url',
                'title',
                'file_path',
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

