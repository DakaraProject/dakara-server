from rest_framework import serializers

from playlist.models import PlaylistEntry, KaraStatus
from library.serializers import (
    SongSerializer,
    SongForPlayerSerializer,
    SecondsDurationField,
)
from users.serializers import (
    UserForPublicSerializer,
)


class PlaylistEntrySerializer(serializers.ModelSerializer):
    """Song serializer in playlist
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
    """Song serializer in playlist
    """
    song = SongSerializer(many=False, read_only=True)
    owner = UserForPublicSerializer(read_only=True)

    # date of play in the future, added manually to the PlaylistEntry object
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
    """Playlist entries with playlist end date
    """
    results = PlaylistEntryReadSerializer(many=True, read_only=True)
    date_end = serializers.DateTimeField(read_only=True)


class PlaylistPlayedEntryReadSerializer(serializers.ModelSerializer):
    """Song serializer in playlist
    """
    song = SongSerializer(many=False, read_only=True)
    owner = UserForPublicSerializer(read_only=True)

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


class PlayerSerializer(serializers.Serializer):
    """Player serializer
    """
    playlist_entry_id = serializers.IntegerField(allow_null=True)
    timing = SecondsDurationField(allow_null=True)
    paused = serializers.BooleanField(default=False)


class PlayerDetailsSerializer(serializers.Serializer):
    """Player serializer with nested playlist_entry and song details
    """
    playlist_entry = serializers.SerializerMethodField()
    timing = SecondsDurationField(allow_null=True)
    paused = serializers.BooleanField(default=False)

    def get_playlist_entry(self, player):
        """Return the playlist entry of the player

        Return it from the playlist entry id stored in the player.
        """
        if player.playlist_entry_id is not None:
            entry = PlaylistEntry.objects.get(id=player.playlist_entry_id)
            return PlaylistPlayedEntryReadSerializer(
                entry,
                context=self.context
            ).data

        return None


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


class PlayerErrorsPoolSerializer(serializers.Serializer):
    """Player errors sent to the client
    """
    id = serializers.IntegerField()
    song = SongSerializer(many=False, read_only=True)
    error_message = serializers.CharField(max_length=255)


class KaraStatusSerializer(serializers.ModelSerializer):
    """Current status of the kara
    """

    class Meta:
        model = KaraStatus
        fields = (
            'status',
        )


class DigestSerializer(serializers.Serializer):
    """Combine player info and kara status
    """
    player_status = PlayerDetailsSerializer()
    player_manage = PlayerCommandSerializer()
    player_errors = PlayerErrorsPoolSerializer(many=True)
    kara_status = KaraStatusSerializer()
