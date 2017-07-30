from django.db import models
from datetime import timedelta
from users.models import DakaraUser


class PlaylistEntry(models.Model):
    """ Class for a song in playlist
    """
    song = models.ForeignKey('library.Song', null=False)
    date_created = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(DakaraUser, null=False)

    def __str__(self):
        return str(self.song)


class Player:
    """ Class for player representation in the server
    """

    def __init__(
            self,
            playlist_entry_id=None,
            timing=timedelta(),
            paused=False
            ):
        self.playlist_entry_id = playlist_entry_id
        self.timing = timing
        self.paused = paused


class PlayerCommand:
    """ Class for user commands to the player
    """

    def __init__(
            self,
            pause=False,
            skip=False
            ):
        self.pause = pause
        self.skip = skip
