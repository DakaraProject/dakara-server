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
    song = models.ForeignKey('library.Song', null=False,
                             on_delete=models.CASCADE)
    date_created = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(DakaraUser, null=False,
                              on_delete=models.CASCADE)
    was_played = models.BooleanField(default=False, null=False)
    date_played = models.DateTimeField(null=True)

    class Meta(OrderedModel.Meta):
        pass

    def __str__(self):
        return "{} (for {})".format(
            self.song,
            self.owner.username
        )

    @classmethod
    def get_playing(cls):
        playlist = cls.objects.filter(
            was_played=False, date_played__isnull=False
        )

        if not playlist:
            return None

        if playlist.count() > 1:
            entries_str = ', '.join([str(e) for e in playlist])

            raise RuntimeError("It seems that several playlist entries are"
                               " playing at the same time: {}"
                               .format(entries_str))

        return playlist.first()

    @classmethod
    def get_playlist(cls):
        queryset = cls.objects.exclude(
            models.Q(was_played=True) | models.Q(date_played__isnull=False)
        )

        return queryset

    @classmethod
    def get_playlist_played(cls):
        playlist = cls.objects.filter(
            was_played=True
        )

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

        # update the player
        player = Player(playlist_entry=self, in_transition=True)
        player.save()

        return player

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

        # update the player
        player = Player()
        player.save()

        return player


class Karaoke(models.Model):
    """Current kara

    Unique for now.
    """
    STOP = "stop"
    PLAY = "play"
    PAUSE = "pause"
    STATUSES = (
        (STOP, "Stop"),
        (PLAY, "Play"),
        (PAUSE, "Pause")
    )

    status = models.CharField(
        max_length=5,
        choices=STATUSES,
        default=PLAY,
        null=False,
    )
    date_stop = models.DateTimeField(null=True)

    def __str__(self):
        return "In {} mode{}".format(
            self.status,
            " will stop at {}".format(self.date.stop) if self.date_stop else ""
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
    playlist_entry = models.ForeignKey(PlaylistEntry, null=False,
                                       on_delete=models.CASCADE)
    error_message = models.CharField(max_length=255)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.playlist_entry)


class Player:
    """Player representation in the server

    This object is not stored in database, but lives within Django memory
    cache. Please use the `update` method to change its attributes.
    """
    PLAYER_NAME = 'player'

    PLAYING_TRANSITION = 'playing_transition'
    PLAYING_SONG = 'playing_song'
    FINISHED = 'finished'
    COULD_NOT_PLAY = 'could_not_play'
    STATUSES = (
        (PLAYING_TRANSITION, "Playing transition"),
        (PLAYING_SONG, "Playing song"),
        (FINISHED, "Finished"),
        (COULD_NOT_PLAY, "Could not play")
    )

    def __init__(
        self,
        playlist_entry_id=None,
        timing=timedelta(),
        paused=False,
        in_transition=False,
        date=None,
        playlist_entry=None,
        status=None,
    ):
        self.playlist_entry_id = playlist_entry_id
        self.timing = timing
        self.paused = paused
        self.in_transition = in_transition
        self.date = None

        # at least set the date
        self.update(playlist_entry=playlist_entry, date=date, status=status)

    def __eq__(self, other):
        fields = ('playlist_entry_id', 'timing', 'paused', 'in_transition',
                  'date')

        return all(getattr(self, field) == getattr(other, field)
                   for field in fields)

    def update(self, playlist_entry=None, date=None, status=None, **kwargs):
        """Update the player and set date"""
        # set normal attributes
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

        # set specific attributes
        self.date = date or datetime.now(tz)

        if playlist_entry:
            # initialize with the setter method
            self.playlist_entry = playlist_entry

        if status == self.STARTING:
            self.in_transition = True

    @property
    def playlist_entry(self):
        if self.playlist_entry_id is None:
            playlist_entry = None

        else:
            playlist_entry = PlaylistEntry.objects.get(
                pk=self.playlist_entry_id)

        playlist_entry_database = PlaylistEntry.get_playing()

        # ensure that the playlist entry of the player is designated to play
        if playlist_entry != playlist_entry_database:
            raise RuntimeError("The player is playing something inconsistent: "
                               "'{}' instead of '{}'"
                               .format(playlist_entry,
                                       playlist_entry_database))

        return playlist_entry

    @playlist_entry.setter
    def playlist_entry(self, entry):
        self.playlist_entry_id = entry.id

    @playlist_entry.deleter
    def playlist_entry(self):
        self.playlist_entry_id = None

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
        self.update(
            playlist_entry_id=None,
            timing=timedelta(),
            paused=False,
            in_transition=False,
        )

    def __repr__(self):
        return "<{}: {}>".format(self.__class__.__name__, self)

    def __str__(self):
        if self.playlist_entry_id is not None:
            return "in {} for '{}' at {}{}".format(
                'pause' if self.paused else 'play',
                self.playlist_entry,
                self.timing,
                ' (in transition)' if self.in_transition else ''
            )

        return "idle"


class PlayerCommand:
    """Commands to the player

    This object is not stored in database, but lives within Django memory
    cache.
    """
    PLAYER_COMMAND_NAME = 'player_command'

    def __init__(
            self,
            pause=False,
            skip=False
    ):
        self.pause = pause
        self.skip = skip

    @classmethod
    def get_or_create(cls):
        """Retrieve the current player commands in cache or create one
        """
        player_command = cache.get(cls.PLAYER_COMMAND_NAME)

        if player_command is None:
            # create a new player commands object
            player_command = cls()

        return player_command

    def save(self):
        """Save player commands in cache
        """
        cache.set(self.PLAYER_COMMAND_NAME, self)

    def __repr__(self):
        return "<{}: {}>".format(self.__class__.__name__, str(self))

    def __str__(self):
        return "requesting {}, {}".format(
            "pause" if self.pause else "no pause",
            "skip" if self.skip else "no skip"
        )
