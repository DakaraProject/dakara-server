from rest_framework import serializers
from library.models import *

class SongSerializer(serializers.HyperlinkedModelSerializer):
    """ Class for song serializer
    """
    class Meta:
        model = Song
        fields = (
                'url',
                'title',
                'file_path',
                'date_created',
                'date_updated',
                )
