from rest_framework import serializers
from playlist.models import PlaylistEntry
from library.serializers import SongSerializer, \
                                SongForPlayerSerializer, \
                                SecondsDurationField

from users.serializers import (
        UserDisplaySerializer,
        )


class PlaylistEntrySerializer(serializers.ModelSerializer):
    """ Class for song serializer in playlist
    """
    owner = serializers.PrimaryKeyRelatedField(
            read_only=True,
            default=serializers.CreateOnlyDefault(
                serializers.CurrentUserDefault()
                )
            )

    class Meta:
        model = PlaylistEntry
        fields = (
                'id',
                'song',
                'date_created',
                'owner',
                )


class PlaylistEntryReadSerializer(serializers.ModelSerializer):
    """ Class for song serializer in playlist
    """
    song = SongSerializer(many=False, read_only=True)
    owner = UserDisplaySerializer(read_only=True)

    class Meta:
        model = PlaylistEntry
        fields = (
                'id',
                'song',
                'date_created',
                'owner',
                )


class PlaylistEntryForPlayerSerializer(serializers.ModelSerializer):
    """ Class for song serializer in playlist
    """
    song = SongForPlayerSerializer(many=False, read_only=True)
    owner = UserDisplaySerializer(read_only=True)

    class Meta:
        model = PlaylistEntry
        fields = (
                'id',
                'song',
                'date_created',
                'owner',
                )


class PlayerSerializer(serializers.Serializer):
    """ Class for Player serializer
    """
    playlist_entry_id = serializers.IntegerField(allow_null=True)
    timing = SecondsDurationField(allow_null=True)
    paused = serializers.BooleanField(default=False)


class PlayerDetailsSerializer(serializers.Serializer):
    """ Class for Player serializer
        with nested playlist_entry and song details
    """
    playlist_entry = serializers.SerializerMethodField()
    timing = SecondsDurationField(allow_null=True)
    paused = serializers.BooleanField(default=False)

    def get_playlist_entry(self, player):
        if player.playlist_entry_id is not None:
            entry = PlaylistEntry.objects.get(id=player.playlist_entry_id)
            return PlaylistEntryReadSerializer(
                    entry,
                    context=self.context
                    ).data

        return None


class PlayerCommandSerializer(serializers.Serializer):
    """ Class for PlayerCommand serializer
    """
    pause = serializers.BooleanField(default=False)
    skip = serializers.BooleanField(default=False)


class PlayerErrorSerializer(serializers.Serializer):
    """ Class for player errors
    """
    playlist_entry = serializers.IntegerField()
    error_message = serializers.CharField(max_length=255)


class PlayerErrorsPoolSerializer(serializers.Serializer):
    """ Class for player errors sent to the client
    """
    id = serializers.IntegerField()
    song = SongSerializer(many=False, read_only=True)
    error_message = serializers.CharField(max_length=255)


class PlayerDetailsCommandErrorsSerializer(serializers.Serializer):
    """ Class combine all player serializers for front
    """
    status = PlayerDetailsSerializer()
    manage = PlayerCommandSerializer()
    errors = PlayerErrorsPoolSerializer(many=True)
