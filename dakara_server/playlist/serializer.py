from rest_framework import serializers
from library.models import *
from library.communications import *

class PlaylistEntrySerializer(serializers.ModelSerializer):
    """ Class for song serializer in playlist
    """
    class meta:
        model = PlaylistEntry
        fields = (
                'song',
                'date_created',
                )

class PlayerSerializer(serializers.ModelSerializer):
    """ Class for communication with the player
    """
    class Meta:
        model = Player

class PlayerStatusSerializer(serializers.Serializer):
    """ Serializer for status communication from the player to the server
    """
    song_id = serializers.IntegerField(null=True)
    timing = serializers.DurationField(null=True)

class PlayerCommandSerializer(serializers.Serializer):
    """ Serializer for command communication from the server to the player
    """
    pause = serializer.BooleanField(default=False)
    skip = serializers.BooleanField(default=False)
