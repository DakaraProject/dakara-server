from rest_framework import serializers
from playlist.models import *
from library.serializers import *

class PlaylistEntrySerializer(serializers.ModelSerializer):
    """ Class for song serializer in playlist
    """
    class Meta:
        model = PlaylistEntry
        fields = (
                'id',
                'song',
                'date_created',
                )

class PlaylistEntryReadSerializer(serializers.ModelSerializer):
    """ Class for song serializer in playlist
    """
    song = SongSerializer(many=False, read_only=True)
    class Meta:
        model = PlaylistEntry
        fields = (
                'id',
                'song',
                'date_created',
                )

class PlaylistEntryForPlayerSerializer(serializers.ModelSerializer):
    """ Class for song serializer in playlist
    """
    song = SongForPlayerSerializer(many=False, read_only=True)
    class Meta:
        model = PlaylistEntry
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

class PlayerDetailsSerializer(serializers.ModelSerializer):
    """ Class for Player serializer
        with nested playlist_entry and song details
    """

    playlist_entry = PlaylistEntryReadSerializer(many=False,read_only=True)
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

class PlayerErrorSerializer(serializers.Serializer):
    """ Class for player errors
    """
    playlist_entry = serializers.IntegerField()
    error_message = serializers.CharField(max_length=255)
