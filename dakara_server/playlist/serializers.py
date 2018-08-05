from rest_framework import serializers

from playlist.models import PlaylistEntry, KaraStatus, PlayerError
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
    # get related entry field
    playlist_entry = PlaylistPlayedEntryWithDatePlayedSerializer(
        many=False, read_only=True, allow_null=True)

    # set related entry field
    playlist_entry_id = serializers.PrimaryKeyRelatedField(
        write_only=True,
        source='playlist_entry',
        queryset=PlaylistEntry.objects.all(),
        allow_null=True,
        required=True,
    )

    timing = SecondsDurationField()
    paused = serializers.BooleanField()
    in_transition = serializers.BooleanField()
    finished = serializers.BooleanField(write_only=True, required=False)
    date = serializers.DateTimeField(read_only=True)

    def validate_playlist_entry_id(self, playlist_entry):
        current_playlist_entry = PlaylistEntry.get_playing()

        # check the playlist entry is currently playing
        if current_playlist_entry != playlist_entry:
            raise serializers.ValidationError("The playlist entry must be "
                                              "currently playing")

        return playlist_entry


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
        current_playlist_entry = PlaylistEntry.get_playing()

        # check something is playing beforehand
        if current_playlist_entry is None:
            raise serializers.ValidationError("There is no currently playing "
                                              "playlist entry")

        # check the playlist entry is currently playing
        if current_playlist_entry != playlist_entry:
            raise serializers.ValidationError("The playlist entry must be "
                                              "currently playing")

        return playlist_entry


class PlayerCommandSerializer(serializers.Serializer):
    """Player command serializer
    """
    command = serializers.ChoiceField(choices={
        'play': 'play',
        'pause': 'pause',
        'skip': 'skip',
    })


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
    player_errors = PlayerErrorSerializer(many=True)
    kara_status = KaraStatusSerializer()


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
