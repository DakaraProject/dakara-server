from datetime import timedelta

from django.db import models
from django.core.cache import cache

from users.models import DakaraUser


class PlaylistEntry(models.Model):
    """Song in playlist
    """
    song = models.ForeignKey('library.Song', null=False,
                             on_delete=models.CASCADE)
    date_created = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(DakaraUser, null=False,
                              on_delete=models.CASCADE)
    was_played = models.BooleanField(default=False, null=False)
    date_played = models.DateTimeField(null=True)

    def __str__(self):
        return "{} (for {})".format(
            self.song,
            self.owner.username
        )

    @classmethod
    def get_playing(cls):
        playlist = cls.objects.filter(
            was_played=False, date_played__isnull=False
        ).order_by('date_created')

        if not playlist:
            return None

        if playlist.count() > 1:
            songs = ', '.join(["'{}'".format(entry.song)
                               for entry in playlist])

            raise RuntimeError("It seems that several entries are playing at "
                               "the same time: {}".format(songs))

        return playlist.first()

    @classmethod
    def get_playlist(cls):
        queryset = cls.objects.exclude(
            models.Q(was_played=True) | models.Q(date_played__isnull=False)
        ).order_by('date_created')

        return queryset

    @classmethod
    def get_playlist_played(cls):
        playlist = cls.objects.filter(
            was_played=True
        ).order_by('date_created')

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

        playlist.order_by('date_created')

        if not playlist:
            return None

        return playlist.first()


class KaraStatus(models.Model):
    """Current status of the kara

    The status is unique for now.
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

    def __str__(self):
        return "In {} mode".format(self.status)

    @classmethod
    def get_object(cls):
        """Get the first instance of kara status
        """
        kara_status, _ = cls.objects.get_or_create(pk=1)
        return kara_status


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
    cache.
    """
    PLAYER_NAME = 'player'

    def __init__(
            self,
            playlist_entry_id=None,
            timing=timedelta(),
            paused=False
    ):
        self.playlist_entry_id = playlist_entry_id
        self.timing = timing
        self.paused = paused

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
        self.playlist_entry_id = None
        self.timing = timedelta()
        self.paused = False

    def __repr__(self):
        return "<{}: {}>".format(self.__class__.__name__, str(self))

    def __str__(self):
        return "in {} mode".format("pause" if self.paused else "play")


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
