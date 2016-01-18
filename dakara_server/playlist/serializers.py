from rest_framework import serializers
from playlist.models import *

class PlaylistEntrySerializer(serializers.ModelSerializer):
    """ Class for song serializer in playlist
    """
    class Meta:
        model = PlaylistEntry
        depth = 1
        fields = (
                'id',
                'song',
                'date_created',
                )

class PlayerSerializer(serializers.ModelSerializer):
    """ Class for Player serializer
    """
    class Meta:
        model = Player
        fields = (
                'playlist_entry',
                'timing',
                'paused',
                )

class PlayerCommandSerializer(serializers.ModelSerializer):
    """ Class for PlayerCommand serializer
    """
    class Meta:
        model = PlayerCommand
        fields = (
                'pause',
                'skip',
                )
