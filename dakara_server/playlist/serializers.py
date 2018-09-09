from rest_framework import serializers

from playlist.models import PlaylistEntry, Karaoke, PlayerError, Player
from library.models import Song
from library.serializers import (
    SongSerializer,
    SongForPlayerSerializer,
    SecondsDurationField,
)
from users.serializers import (
    UserForPublicSerializer,
)


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
    """Player status serializer
    """
    # Read only fields for front
    playlist_entry = PlaylistPlayedEntryWithDatePlayedSerializer(
        many=False, read_only=True, allow_null=True)

    paused = serializers.BooleanField(read_only=True)
    in_transition = serializers.BooleanField(read_only=True)
    date = serializers.DateTimeField(read_only=True)

    # Write only for the player
    playlist_entry_id = serializers.PrimaryKeyRelatedField(
        write_only=True,
        source='playlist_entry',
        queryset=PlaylistEntry.objects.all(),
        allow_null=True,
    )

    event = serializers.ChoiceField(
        choices=Player.EVENTS,
        write_only=True,
    )

    # Commons fields
    timing = SecondsDurationField(required=False)

    def validate(self, data):
        if 'event' not in data:
            raise serializers.ValidationError("Event is mandatory")

        return data

    def validate_playlist_entry_id(self, playlist_entry):
        next_playlist_entry = PlaylistEntry.get_next()

        if next_playlist_entry != playlist_entry:
            raise serializers.ValidationError("This playlist entry is not"
                                              " supposed to play")

        return playlist_entry

    def validate_event(self, event):
        player = Player.get_or_create()

        # Idle state
        if player.playlist_entry is None:
            if event not in [player.STARTED_TRANSITION, player.COULD_NOT_PLAY]:
                raise serializers.ValidationError("This event should not occur"
                                                  " in this state")

            return event

        # Non idle state

        # These events can occur in any non idle state
        if event in [player.FINISHED, player.PAUSED, player.RESUMED]:
            return event

        # This event should only occur during transition
        if event == player.STARTED_SONG:
            if player.in_transition:
                return event

        raise serializers.ValidationError("This event should not occur"
                                          " in this state")


class PlayerEntryFinishedSerializer(serializers.Serializer):
    """Player finished entry serializer
    """
    # get related entry field
    entry = PlaylistEntrySerializer(many=False, read_only=True)

    # set related entry field
    entry_id = serializers.PrimaryKeyRelatedField(
        write_only=True,
        source='entry',
        queryset=PlaylistEntry.objects.all()
    )


class PlayerErrorSerializer(serializers.ModelSerializer):
    """Player errors
    """
    # get related entry field
    playlist_entry = PlaylistPlayedEntryWithDatePlayedSerializer(
        many=False, read_only=True)

    # set related entry field
    playlist_entry_id = serializers.PrimaryKeyRelatedField(
        write_only=True,
        source='playlist_entry',
        queryset=PlaylistEntry.objects.all()
    )

    class Meta:
        model = PlayerError
        fields = (
            'playlist_entry',
            'playlist_entry_id',
            'error_message'
        )
        read_only_fields = (
            'date_created',
        )

    def validate_playlist_entry_id(self, playlist_entry):
        # check the playlist entry is currently playing or was played
        if playlist_entry != PlaylistEntry.get_playing() and \
           playlist_entry not in PlaylistEntry.get_playlist_played():
            raise serializers.ValidationError("The playlist entry must be "
                                              "currently playing or already "
                                              "played")

        return playlist_entry


class PlayerCommandSerializer(serializers.Serializer):
    """Player command serializer
    """
    command = serializers.ChoiceField(choices=Player.COMMANDS)


class KaraokeSerializer(serializers.ModelSerializer):
    """Current status of the kara
    """

    class Meta:
        model = Karaoke
        fields = (
            'status',
            'date_stop',
        )


class DigestSerializer(serializers.Serializer):
    """Combine player info and kara status
    """
    player_status = PlayerStatusSerializer()  # TODO test this
    player_errors = PlayerErrorSerializer(many=True)
    karaoke = KaraokeSerializer()


class PlaylistReorderSerializer(serializers.Serializer):
    """Requested position of playlist entry
    """
    before_id = serializers.IntegerField(required=False)
    after_id = serializers.IntegerField(required=False)

    def validate(self, data):
        """Check only one field is specified
        """
        if 'before_id' in data and 'after_id' in data:
            raise serializers.ValidationError(
                "Only one field should be specified")

        elif 'before_id' not in data and 'after_id' not in data:
            raise serializers.ValidationError(
                "At least one field should be specified")

        else:
            return data
