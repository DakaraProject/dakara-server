from rest_framework import serializers

from playlist.models import PlaylistEntry
from library.serializers import (
    SongForPlayerSerializer,
    SecondsDurationField,
)
from users.serializers import (
    UserForPublicSerializer,
)


class PlaylistEntrySerializer(serializers.ModelSerializer):
    """Song serializer in playlist
    """
    song = SongForPlayerSerializer(many=False, read_only=True)
    owner = UserForPublicSerializer(read_only=True)

    class Meta:
        model = PlaylistEntry
        fields = (
            'id',
            'song',
            'date_created',
            'owner',
        )
        read_only_fields = (
            'date_created',
        )


class PlayerSerializer(serializers.Serializer):
    """Player serializer
    """
    playlist_entry_id = serializers.IntegerField(allow_null=True)
    timing = SecondsDurationField(allow_null=True)
    paused = serializers.BooleanField(default=False)


class PlayerCommandSerializer(serializers.Serializer):
    """Player command serializer
    """
    pause = serializers.BooleanField(default=False)
    skip = serializers.BooleanField(default=False)


class PlayerErrorSerializer(serializers.Serializer):
    """Player errors
    """
    playlist_entry = serializers.IntegerField()
    error_message = serializers.CharField(max_length=255)
