from datetime import timedelta, datetime

from django.db import models
from django.core.cache import cache
from django.utils import timezone
from ordered_model.models import OrderedModel

from users.models import DakaraUser

tz = timezone.get_default_timezone()


class PlaylistEntry(OrderedModel):
    """Song in playlist
    """

    song = models.ForeignKey("library.Song", null=False, on_delete=models.CASCADE)
    date_created = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(DakaraUser, null=False, on_delete=models.CASCADE)
    was_played = models.BooleanField(default=False, null=False)
    date_played = models.DateTimeField(null=True)

    class Meta(OrderedModel.Meta):
        pass

    def __str__(self):
        return "{} (for {})".format(self.song, self.owner.username)

    @classmethod
    def get_playing(cls):
        playlist = cls.objects.filter(was_played=False, date_played__isnull=False)

        if not playlist:
            return None

        if playlist.count() > 1:
            entries_str = ", ".join([str(e) for e in playlist])

            raise RuntimeError(
                "It seems that several playlist entries are"
                " playing at the same time: {}".format(entries_str)
            )

        return playlist.first()

    @classmethod
    def get_playlist(cls):
        queryset = cls.objects.exclude(
            models.Q(was_played=True) | models.Q(date_played__isnull=False)
        )

        return queryset

    @classmethod
    def get_playlist_played(cls):
        playlist = cls.objects.filter(was_played=True)

        return playlist

    @classmethod
    def get_next(cls, entry_id=None):
        """Retrieve next playlist entry

        Returns the next playlist entry in playlist excluding entry with
        specified id and alredy played songs.
        """
        if entry_id is None:
            playlist = cls.objects.exclude(was_played=True)

        else:
            # do not process a played entry
            if cls.get_playlist_played().filter(pk=entry_id):
                return None

            playlist = cls.get_playlist().exclude(pk=entry_id)

        if not playlist:
            return None

        return playlist.first()

    def set_playing(self):
        """The playlist entry has started to play

        Returns:
            Player: the current player.
        """
        # check that no other playlist entry is playing
        if self.get_playing() is not None:
            raise RuntimeError("A playlist entry is currently in play")

        # set the playlist entry
        self.date_played = datetime.now(tz)
        self.save()

    def set_finished(self):
        """The playlist entry has finished

        Returns:
            Player: the current player.
        """
        # check the current playlist entry is in play
        if self != self.get_playing():
            raise RuntimeError("This playlist entry is not playing")

        # set the playlist entry
        self.was_played = True
        self.save()


class Karaoke(models.Model):
    """Current kara

    Unique for now.
    """

    ongoing = models.BooleanField(default=True)
    can_add_to_playlist = models.BooleanField(default=True)
    player_play_next_song = models.BooleanField(default=True)
    date_stop = models.DateTimeField(null=True)
    channel_name = models.CharField(max_length=255, null=True)

    def __str__(self):
        return "{}{}".format(
            "Ongoing" if self.ongoing else "Stopped",
            " will stop at {}".format(self.date.stop) if self.date_stop else "",
        )

    @classmethod
    def get_object(cls):
        """Get the first instance of kara status
        """
        karaoke, _ = cls.objects.get_or_create(pk=1)
        return karaoke


class PlayerError(models.Model):
    """Entries that failed to play
    """

    playlist_entry = models.ForeignKey(
        PlaylistEntry, null=False, on_delete=models.CASCADE
    )
    error_message = models.CharField(max_length=255)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.playlist_entry)


class Player:
    """Player representation in the server

    This object is not stored in database, but lives within Django memory
    cache. Please use the `update` method to change its attributes.
    """

    PLAYER_NAME = "player"

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

    def __init__(
        self, timing=timedelta(), paused=False, in_transition=False, date=None
    ):
        self.timing = timing
        self.paused = paused
        self.in_transition = in_transition
        self.date = None

        # at least set the date
        self.update(date=date)

    def __eq__(self, other):
        fields = ("timing", "paused", "in_transition", "date")

        return all(getattr(self, field) == getattr(other, field) for field in fields)

    def update(self, date=None, **kwargs):
        """Update the player and set date"""
        # set normal attributes
        for key, value in kwargs.items():
            if hasattr(self, key) and key != "playlist_entry":
                setattr(self, key, value)

        # set specific attributes
        self.date = date or datetime.now(tz)

    @property
    def playlist_entry(self):
        return PlaylistEntry.get_playing()

    @classmethod
    def get_or_create(cls):
        """Retrieve the current player in cache or create one
        """
        player = cache.get(cls.PLAYER_NAME)

        if player is None:
            # create a new player object
            player = cls()

        return player

    def save(self):
        """Save player in cache
        """
        cache.set(self.PLAYER_NAME, self)

    def reset(self):
        """Reset the player to its initial state
        """
        self.update(timing=timedelta(), paused=False, in_transition=False)

    def __repr__(self):
        return "<{}: {}>".format(self.__class__.__name__, self)

    def __str__(self):
        if self.playlist_entry is not None:
            return "in {} for '{}' at {}{}".format(
                "pause" if self.paused else "play",
                self.playlist_entry,
                self.timing,
                " (in transition)" if self.in_transition else "",
            )

        return "idle"
