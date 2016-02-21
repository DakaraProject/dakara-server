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

class PlayerSerializer(serializers.Serializer):
    """ Class for Player serializer
    """
    playlist_entry_id = serializers.IntegerField(allow_null=True)
    timing = serializers.DurationField(allow_null=True)
    paused = serializers.BooleanField(default=False)


class PlayerDetailsSerializer(serializers.Serializer):
    """ Class for Player serializer
        with nested playlist_entry and song details
    """
    playlist_entry = serializers.SerializerMethodField()
    timing = serializers.DurationField(allow_null=True)
    paused = serializers.BooleanField(default=False)

    def get_playlist_entry(self, player):
        if player.playlist_entry_id is not None:
            entry = PlaylistEntry.objects.get(id=player.playlist_entry_id)
            return PlaylistEntryReadSerializer(entry, context=self.context).data

        return None


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
