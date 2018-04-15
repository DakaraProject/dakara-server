from rest_framework import serializers
from playlist.models import PlaylistEntry, KaraStatus
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
    date_play = serializers.DateTimeField(read_only=True)

    class Meta:
        model = PlaylistEntry
        fields = (
                'id',
                'song',
                'date_created',
                'owner',
                'date_play',
                )


class PlaylistEntriesReadSerializer(serializers.Serializer):
    """ Class for playlist entries with playlist end date
    """
    results = PlaylistEntryReadSerializer(many=True, read_only=True)
    date_end = serializers.DateTimeField(read_only=True)


class PlaylistPlayedEntryReadSerializer(serializers.ModelSerializer):
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
                'date_played'
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
            return PlaylistPlayedEntryReadSerializer(
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


class KaraStatusSerializer(serializers.ModelSerializer):
    """ Class for the current status of the kara
    """

    class Meta:
        model = KaraStatus
        fields = (
                'status',
                )


class DigestSerializer(serializers.Serializer):
    """ Class combine player info and kara status
    """
    player_status = PlayerDetailsSerializer()
    player_manage = PlayerCommandSerializer()
    player_errors = PlayerErrorsPoolSerializer(many=True)
    kara_status = KaraStatusSerializer()
