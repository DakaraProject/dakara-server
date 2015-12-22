from rest_framework import serializers
from playlist.models import *
from playlist.communications import *

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
    song_id = serializers.IntegerField()
    timing = serializers.DurationField()

class PlayerCommandSerializer(serializers.Serializer):
    """ Serializer for command communication from the server to the player
    """
    pause = serializers.BooleanField(default=False)
    skip = serializers.BooleanField(default=False)
