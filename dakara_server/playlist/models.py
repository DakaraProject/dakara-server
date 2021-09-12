import textwrap
from datetime import datetime, timedelta

from django.db import models
from django.db.utils import OperationalError
from django.utils import timezone
from ordered_model.models import OrderedModel, OrderedModelManager

from internal.cache_model import CacheModel
from users.models import DakaraUser

tz = timezone.get_default_timezone()


class PlaylistManager(OrderedModelManager):
    """Manager of playlist objects."""

    def get_playing(self):
        """Get the current playlist entry."""
        playlist = self.filter(was_played=False, date_played__isnull=False)

        if not playlist:
            return None

        if playlist.count() > 1:
            entries_str = ", ".join([str(e) for e in playlist])

            raise RuntimeError(
                "It seems that several playlist entries are"
                " playing at the same time: {}".format(entries_str)
            )

        return playlist.first()

    def get_playlist(self):
        """Get the playlist of ongoing entries."""
        queryset = self.exclude(
            models.Q(was_played=True) | models.Q(date_played__isnull=False)
        )

        return queryset

    def get_playlist_played(self):
        """Get the playlist of passed entries."""
        playlist = self.filter(was_played=True)

        return playlist

    def get_next(self, entry_id=None):
        """Get next playlist entry.

        Returns the next playlist entry in playlist excluding entry with
        specified id and alredy played songs.

        Args:
            entry_id (int): If specified, exclude the corresponding playlist
                entry.
        """
        if entry_id is None:
            playlist = self.exclude(was_played=True)

        else:
            # do not process a played entry
            if self.get_playlist_played().filter(pk=entry_id):
                return None

            playlist = self.get_playlist().exclude(pk=entry_id)

        if not playlist:
            return None

        return playlist.first()


class PlaylistEntry(OrderedModel):
    """Song in playlist."""

    objects = PlaylistManager()

    song = models.ForeignKey("library.Song", null=False, on_delete=models.CASCADE)
    use_instrumental = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(DakaraUser, null=False, on_delete=models.CASCADE)
    was_played = models.BooleanField(default=False, null=False)
    date_played = models.DateTimeField(null=True)

    class Meta(OrderedModel.Meta):
        pass

    def __str__(self):
        return "{} (for {})".format(self.song, self.owner)

    def set_playing(self):
        """The playlist entry has started to play."""
        # check that no other playlist entry is playing
        if PlaylistEntry.objects.get_playing() is not None:
            raise RuntimeError("A playlist entry is currently in play")

        # set the playlist entry
        self.date_played = datetime.now(tz)
        self.save()

    def set_finished(self):
        """The playlist entry has finished."""
        # check the current playlist entry is in play
        if self != PlaylistEntry.objects.get_playing():
            raise RuntimeError("This playlist entry is not playing")

        # set the playlist entry
        self.was_played = True
        self.save()


class KaraokeManager(models.Manager):
    """Manager of karaoke objects.

    Only one karaoke object can exist for now.
    """

    def get_object(self):
        """Get the first instance of kara status."""
        karaoke, _ = self.get_or_create(pk=1)
        return karaoke

    def clean_channel_names(self):
        """Remove all channel names."""
        for karaoke in self.all():
            karaoke.channel_name = None
            karaoke.save()


def clean_channel_names():
    try:
        Karaoke.objects.clean_channel_names()

    # if database does not exist when checking date stop, abort the function
    # this case occurs on startup before running tests
    except OperationalError:
        return


class Karaoke(models.Model):
    """Current kara."""

    objects = KaraokeManager()

    ongoing = models.BooleanField(default=True)
    can_add_to_playlist = models.BooleanField(default=True)
    player_play_next_song = models.BooleanField(default=True)
    date_stop = models.DateTimeField(null=True)
    channel_name = models.CharField(max_length=255, null=True)

    def __str__(self):
        return f"karaoke {self.pk}"


class PlayerError(models.Model):
    """Entries that failed to play."""

    playlist_entry = models.ForeignKey(
        PlaylistEntry, null=False, on_delete=models.CASCADE
    )
    error_message = models.CharField(max_length=255)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "{}: {}".format(
            self.playlist_entry, textwrap.shorten(self.error_message, 50)
        )


class Player(CacheModel):
    """Player representation in the server.

    This object is not stored in database, but lives within Django cache.
    """

    timing = models.DurationField(default=timedelta())
    paused = models.BooleanField(default=False)
    in_transition = models.BooleanField(default=False)
    date = models.DateTimeField(auto_now=True)

    STARTED_TRANSITION = "started_transition"
    STARTED_SONG = "started_song"
    FINISHED = "finished"
    COULD_NOT_PLAY = "could_not_play"
    PAUSED = "paused"
    RESUMED = "resumed"
    EVENTS = (
        (STARTED_TRANSITION, "Started transition"),
        (STARTED_SONG, "Started song"),
        (FINISHED, "Finished"),
        (COULD_NOT_PLAY, "Could not play"),
        (PAUSED, "Paused"),
        (RESUMED, "Resumed"),
    )

    PLAY = "play"
    PAUSE = "pause"
    SKIP = "skip"
    COMMANDS = ((PLAY, "Play"), (PAUSE, "Pause"), (SKIP, "Skip"))

    @property
    def playlist_entry(self):
        return PlaylistEntry.objects.get_playing()

    def __str__(self):
        return f"player {self.pk}"
