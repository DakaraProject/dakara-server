from datetime import timedelta

from django.db import models
from django.core.cache import cache
from ordered_model.models import OrderedModel

from users.models import DakaraUser


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
    def get_next(cls, id):
        """Retrieve next playlist entry

        Returns the next playlist entry in playlist excluding entry with
        specified id and alredy played songs.
        """
        playlist = cls.objects.exclude(
            models.Q(pk=id) | models.Q(was_played=True)
        )

        if not playlist:
            return None

        playlist_entry = playlist[0]

        return playlist_entry


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

    def __str__(self):
        return str("in {} mode".format(self.status))

    @classmethod
    def get_object(cls):
        """Get the first instance of kara status
        """
        karaoke, _ = cls.objects.get_or_create(pk=1)
        return karaoke


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


class PlayerError:
    """Error encountered by the player

    Each error is stored in cache for `PLAYER_ERROR_TIME_OF_LIFE` seconds and
    will be then removed. Each of them has a distinct name made from the
    `PLAYER_ERROR_PATTERN` pattern with its `id` as a suffix.

    The error is not stored automatically in memory when created. The `save`
    method has to be called for this.

    This class should not be manipulated directly outside of this module.

    This object is not stored in database, but lives within Django memory
    cache.
    """
    PLAYER_ERROR_PATTERN = "player_error_{}"
    PLAYER_ERROR_TIME_OF_LIFE = 10

    def __init__(self, id, song, error_message):
        self.id = id
        self.song = song
        self.error_message = error_message

    @classmethod
    def get(cls, id):
        """Retrieve an error from the cache by its ID if still present
        """
        player_error_name = cls.PLAYER_ERROR_PATTERN.format(id)
        return cache.get(player_error_name)

    def save(self):
        """Save the object in cache for a certain amount of time
        """
        player_error_name = self.PLAYER_ERROR_PATTERN.format(self.id)
        cache.set(player_error_name, self, self.PLAYER_ERROR_TIME_OF_LIFE)

    def __repr__(self):
        return "<{}: {}>".format(self.__class__.__name__, str(self))

    def __str__(self):
        return "error {}".format(self.id)


class PlayerErrorsPool:
    """Class to manage player errors

    The class manages the pool of errors and the errors themselve. Both of them
    are stored in cache.

    Each method should be followed by the `save` method, otherwize the cache is
    not updated.

    This object is not stored in database, it is not stored at all.
    """
    PLAYER_ERROR_POOL_NAME = 'player_error_pool'

    def __init__(self, ids_pool=[], count=0):
        self.ids_pool = ids_pool
        self.count = count

        # temporary pool for new errors
        self.temp_pool = []

    @classmethod
    def get_or_create(cls):
        """Retrieve the current player errors pool in cache or create one
        """
        pool = cache.get(cls.PLAYER_ERROR_POOL_NAME)

        if pool is None:
            # create a new pool
            pool = cls()

        else:
            # clean old errors
            pool.clean()
            pool.save()

        return pool

    def save(self):
        """Save player errors pool in cache
        """
        cache.set(self.PLAYER_ERROR_POOL_NAME, self)

        # save new errors
        for error in self.temp_pool:
            error.save()

        # purge new errors list
        self.temp_pool = []

    def add(self, song, error_message):
        """Add one error to the errors pool
        """
        error = PlayerError(self.count, song, error_message)
        self.temp_pool.append(error)
        self.ids_pool.append(self.count)
        self.count += 1

    def clean(self):
        """Remove old errors from pool
        """
        self.ids_pool = [
            id for id in self.ids_pool
            if PlayerError.get(id) is not None
        ]

    def dump(self):
        """Gives the pool as a list
        """
        return [PlayerError.get(id) for id in self.ids_pool]

    def __repr__(self):
        return "<{}: {}>".format(self.__class__.__name__, str(self))

    def __str__(self):
        return "with {} error(s)".format(self.count)
