from rest_framework import serializers

from playlist.models import PlaylistEntry, KaraStatus
from library.models import Song
from library.serializers import (
    SongSerializer,
    SecondsDurationField,
)
from users.serializers import (
    UserForPublicSerializer,
)
from playlist import serializers_device as device # noqa F401
from playlist.serializers_device import PlayerCommandSerializer


class PlaylistEntrySerializer(serializers.ModelSerializer):
    """Playlist entry serializer
    """
    # get related owner field
    # auto-set related owner field
    owner = UserForPublicSerializer(read_only=True,
                                    default=serializers.CurrentUserDefault())

    # get related song field
    song = SongSerializer(many=False, read_only=True)

    # set related song field
    song_id = serializers.PrimaryKeyRelatedField(
        write_only=True,
        source='song',
        queryset=Song.objects.all()
    )

    class Meta:
        model = PlaylistEntry
        fields = (
            'id',
            'date_created',
            'owner',
            'song',
            'song_id',
        )
        read_only_fields = (
            'date_created',
        )


class PlaylistEntryWithDatePlaySerializer(PlaylistEntrySerializer):
    """Playlist entry serializer

    Reserved for song that will be played.
    """
    # date of play in the future, added manually to the PlaylistEntry object
    date_play = serializers.DateTimeField(read_only=True)

    class Meta(PlaylistEntrySerializer.Meta):
        fields = (
            'id',
            'date_created',
            'date_play',
            'owner',
            'song',
        )


class PlaylistPlayedEntryWithDatePlayedSerializer(PlaylistEntrySerializer):
    """Playlist entry serializer

    Reserved for song that were played.
    """

    class Meta(PlaylistEntrySerializer.Meta):
        fields = (
            'id',
            'date_created',
            'date_played',
            'owner',
            'song',
        )
        read_only_fields = (
            'date_created',
            'date_played',
        )


class PlaylistEntriesWithDateEndSerializer(serializers.Serializer):
    """Playlist entries with playlist end date
    """
    results = PlaylistEntryWithDatePlaySerializer(many=True, read_only=True)
    date_end = serializers.DateTimeField(read_only=True)


class PlayerStatusSerializer(serializers.Serializer):
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
            return PlaylistPlayedEntryWithDatePlayedSerializer(
                entry,
                context=self.context
            ).data

        return None


class PlayerErrorSerializer(serializers.Serializer):
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
    player_status = PlayerStatusSerializer()
    player_manage = PlayerCommandSerializer()
    player_errors = PlayerErrorSerializer(many=True)
    kara_status = KaraStatusSerializer()
