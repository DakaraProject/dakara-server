from datetime import datetime

from django.utils import timezone
from rest_framework import serializers

from library.models import Song
from library.serializers import (
    SecondsDurationField,
    SongForDigestSerializer,
    SongForPlayerSerializer,
    SongSerializer,
)
from playlist.models import Karaoke, Player, PlayerError, PlayerToken, PlaylistEntry
from users.serializers import UserForPublicSerializer

tz = timezone.get_default_timezone()


class PlaylistEntrySerializer(serializers.ModelSerializer):
    """Playlist entry serializer."""

    # get related owner field
    # auto-set related owner field
    owner = UserForPublicSerializer(read_only=True)

    # get related song field
    song = SongSerializer(many=False, read_only=True)

    # set related song field
    song_id = serializers.PrimaryKeyRelatedField(
        write_only=True, source="song", queryset=Song.objects.all()
    )

    class Meta:
        model = PlaylistEntry
        fields = (
            "id",
            "date_created",
            "owner",
            "song",
            "song_id",
            "use_instrumental",
            "date_play",
        )
        read_only_fields = ("date_created", "date_play")

    def validate(self, data):
        if data.get("use_instrumental") and not data["song"].has_instrumental:
            raise serializers.ValidationError("Song does not have instrumental")

        return data


class PlaylistEntryForPlayerSerializer(serializers.ModelSerializer):
    """Song serializer in playlist."""

    song = SongForPlayerSerializer(many=False, read_only=True)
    owner = UserForPublicSerializer(read_only=True)

    class Meta:
        model = PlaylistEntry
        fields = ("id", "song", "date_created", "owner", "use_instrumental")
        read_only_fields = ("date_created",)


class PlaylistEntryForDigestSerializer(serializers.ModelSerializer):
    """Played playlist entry serializer for playlist digest info."""

    song = SongForDigestSerializer(many=False, read_only=True)

    class Meta:
        model = PlaylistEntry
        fields = (
            "id",
            "song",
            "use_instrumental",
            "date_play",
            "was_played",
            "owner",
        )
        read_only_fields = (
            "id",
            "song",
            "use_instrumental",
            "date_play",
            "was_played",
            "owner",
        )


class PlaylistEntriesWithDateEndSerializer(serializers.Serializer):
    """Playlist entries with playlist end date."""

    results = PlaylistEntrySerializer(many=True, read_only=True)
    date_end = serializers.DateTimeField(read_only=True)


class PlayerStatusSerializer(serializers.ModelSerializer):
    """Player status serializer."""

    # Read only fields for front
    playlist_entry = PlaylistEntrySerializer(
        many=False, read_only=True, allow_null=True
    )

    # Write only for the player
    playlist_entry_id = serializers.PrimaryKeyRelatedField(
        write_only=True,
        source="playlist_entry",
        queryset=PlaylistEntry.objects.all(),
        allow_null=True,
    )

    event = serializers.ChoiceField(choices=Player.EVENTS, write_only=True)

    # Common fields
    timing = SecondsDurationField(required=False)

    class Meta:
        model = Player
        fields = (
            "date",
            "event",
            "in_transition",
            "paused",
            "playlist_entry",
            "playlist_entry_id",
            "timing",
        )
        read_only_fields = ("paused", "in_transition", "date", "playlist_entry")
        to_update_fields = ("timing",)

    def to_representation(self, instance, *args, **kwargs):
        # override the representation method to force recalculation of player
        # timing
        self.recalculate_timing(instance)
        return super().to_representation(instance, *args, **kwargs)

    def recalculate_timing(self, player):
        """Manually update the player timing.

        Args:
            player (playlist.models.Player): Instance of the current player.
        """
        if player is None or not isinstance(player, Player):
            return

        now = datetime.now(tz)
        if player.playlist_entry:
            if not player.paused and not player.in_transition:
                player.timing += now - player.date
                player.date = now

    def update(self, instance, validated_data):
        # filter out read only values
        curated_data = {
            k: v for k, v in validated_data.items() if k in self.Meta.to_update_fields
        }
        return super().update(instance, curated_data)

    def validate(self, data):
        if "event" not in data:
            raise serializers.ValidationError("Event is mandatory")

        return data

    def validate_playlist_entry_id(self, playlist_entry):
        next_playlist_entry = PlaylistEntry.objects.get_next()

        if next_playlist_entry != playlist_entry:
            raise serializers.ValidationError(
                "This playlist entry is not supposed to play"
            )

        return playlist_entry

    def validate_event(self, event):
        karaoke = Karaoke.objects.get_object()
        player, _ = Player.cache.get_or_create(karaoke=karaoke)

        # Idle state
        if player.playlist_entry is None:
            if event not in [player.STARTED_TRANSITION, player.COULD_NOT_PLAY]:
                raise serializers.ValidationError(
                    "The '{}' event should not occur when the player is idle".format(
                        event
                    )
                )

            return event

        # Non idle state

        # These events can occur in any non idle state
        if event in [
            player.FINISHED,
            player.PAUSED,
            player.RESUMED,
            player.UPDATED_TIMING,
        ]:
            return event

        # This event should only occur during transition
        if event == player.STARTED_SONG:
            if player.in_transition:
                return event

        raise serializers.ValidationError(
            "The '{}' event should not occur when the player is not idle".format(event)
        )


class PlayerEntryFinishedSerializer(serializers.Serializer):
    """Player finished entry serializer."""

    # get related entry field
    entry = PlaylistEntrySerializer(many=False, read_only=True)

    # set related entry field
    entry_id = serializers.PrimaryKeyRelatedField(
        write_only=True, source="entry", queryset=PlaylistEntry.objects.all()
    )


class PlayerErrorSerializer(serializers.ModelSerializer):
    """Player errors."""

    # get related entry field
    playlist_entry = PlaylistEntrySerializer(many=False, read_only=True)

    # set related entry field
    playlist_entry_id = serializers.PrimaryKeyRelatedField(
        write_only=True, source="playlist_entry", queryset=PlaylistEntry.objects.all()
    )

    class Meta:
        model = PlayerError
        fields = (
            "playlist_entry",
            "playlist_entry_id",
            "error_message",
            "date_created",
        )
        read_only_fields = ("date_created",)

    def validate_playlist_entry_id(self, playlist_entry):
        # check the playlist entry is currently playing, or was played, or is
        # about to be played
        if not (
            playlist_entry == PlaylistEntry.objects.get_playing()
            or playlist_entry in PlaylistEntry.objects.get_playlist_played()
            or PlaylistEntry.objects.get_playing() is None
            and playlist_entry == PlaylistEntry.objects.get_next()
        ):
            raise serializers.ValidationError(
                "The playlist entry must be currently playing, or already "
                "played, or about to be played"
            )

        return playlist_entry


class PlayerErrorForDigestSerializer(serializers.ModelSerializer):
    """Player error serializers for playlist digest info."""

    playlist_entry = PlaylistEntryForDigestSerializer(many=False, read_only=True)

    class Meta:
        model = PlayerError
        fields = (
            "id",
            "playlist_entry",
            "error_message",
            "date_created",
        )
        read_only_fields = ("id", "playlist_entry", "error_message", "date_created")


class PlayerCommandSerializer(serializers.Serializer):
    """Player command serializer."""

    command = serializers.ChoiceField(choices=Player.COMMANDS)


class KaraokeSerializer(serializers.ModelSerializer):
    """Current status of the kara."""

    class Meta:
        model = Karaoke
        fields = (
            "id",
            "ongoing",
            "can_add_to_playlist",
            "player_play_next_song",
            "date_stop",
        )


class PlayerTokenSerializer(serializers.ModelSerializer):
    karaoke_id = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = PlayerToken
        fields = (
            "karaoke_id",
            "key",
        )


class DigestSerializer(serializers.Serializer):
    """Combine player info and kara status."""

    player_status = PlayerStatusSerializer()
    karaoke = KaraokeSerializer()
    player_errors = PlayerErrorForDigestSerializer(many=True)
    playlist_entries = PlaylistEntryForDigestSerializer(many=True)


class PlaylistReorderSerializer(serializers.Serializer):
    """Requested position of playlist entry."""

    before_id = serializers.IntegerField(required=False)
    after_id = serializers.IntegerField(required=False)

    def validate(self, data):
        """Check only one field is specified."""
        if "before_id" in data and "after_id" in data:
            raise serializers.ValidationError("Only one field should be specified")

        elif "before_id" not in data and "after_id" not in data:
            raise serializers.ValidationError("At least one field should be specified")

        else:
            return data
