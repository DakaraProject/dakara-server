from django.db import models
from datetime import timedelta
from users.models import DakaraUser
from django.core.cache import cache


class PlaylistEntry(models.Model):
    """ Class for a song in playlist
    """
    song = models.ForeignKey('library.Song', null=False)
    date_created = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(DakaraUser, null=False)

    def __str__(self):
        return str(self.song)

    @classmethod
    def get_next(cls, id):
        """ Returns the next playlist entry in playlist
            excluding entry with specified id
        """
        playlist = cls.objects.exclude(pk=id).order_by('date_created')

        if not playlist:
            return None

        playlist_entry = playlist[0]

        return playlist_entry


class Player:
    """ Class for player representation in the server
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
        """ Retrieve the current player in cache or create one
        """
        player = cache.get(cls.PLAYER_NAME)

        if player is None:
            # create a new player object
            player = cls()

        return player

    def save(self):
        """ Save player in cache
        """
        cache.set(self.PLAYER_NAME, self)


class PlayerCommand:
    """ Class for user commands to the player
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
        """ Retrieve the current player commands in cache or create one
        """
        player_command = cache.get(cls.PLAYER_COMMAND_NAME)

        if player_command is None:
            # create a new player commands object
            player_command = cls()

        return player_command

    def save(self):
        """ Save player commands in cache
        """
        cache.set(self.PLAYER_COMMAND_NAME, self)


class PlayerError:
    """ Class for error encountered by the player

        Each error is stored in cache for `PLAYER_ERROR_TIME_OF_LIFE` seconds
        and will be then removed. Each of them has a distinct name made from the
        `PLAYER_ERROR_PATTERN` pattern with its `id` as a suffix.

        The error is not stored automatically in memory when created. The `save`
        method has to be called for this.

        This class should not be manipulated directly outside of this module.
    """
    PLAYER_ERROR_PATTERN = "player_error_{}"
    PLAYER_ERROR_TIME_OF_LIFE = 10

    def __init__(self, id, song, error_message):
        self.id = id
        self.song = song
        self.error_message = error_message

    @classmethod
    def get(cls, id):
        """ Retrieve an error from the cache by its ID if still present
        """
        player_error_name = cls.PLAYER_ERROR_PATTERN.format(id)
        return cache.get(player_error_name)

    def save(self):
        """ Save the object in cache for a certain amount of time
        """
        player_error_name = self.PLAYER_ERROR_PATTERN.format(self.id)
        cache.set(player_error_name, self, self.PLAYER_ERROR_TIME_OF_LIFE)


class PlayerErrorsPool:
    """ Class to manage player errors

        The class manages the pool of errors and the errors themselve. Both of
        them are stored in cache.

        Each method should be followed by the `save` method, otherwize the cache
        is not updated.
    """
    PLAYER_ERROR_POOL_NAME = 'player_error_pool'

    def __init__(self, ids_pool=[], count=0):
        self.ids_pool = ids_pool
        self.count = count

        # temporary pool for new errors
        self.temp_pool = []

    @classmethod
    def get_or_create(cls):
        """ Retrieve the current player errors pool in cache or create one
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
        """ Save player errors pool in cache
        """
        cache.set(self.PLAYER_ERROR_POOL_NAME, self)

        # save new errors
        for error in self.temp_pool:
            error.save()

        # purge new errors list
        self.temp_pool = []

    def add(self, song, error_message):
        """ Add one error to the errors pool
        """
        error = PlayerError(self.count, song, error_message)
        self.temp_pool.append(error)
        self.ids_pool.append(self.count)
        self.count += 1

    def clean(self):
        """ Remove old errors from pool
        """
        self.ids_pool = [
                id for id in self.ids_pool
                if PlayerError.get(id) is not None
                ]

    def dump(self):
        """ Gives the pool as a list
        """
        return [PlayerError.get(id) for id in self.ids_pool]
