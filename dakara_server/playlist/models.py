from django.db import models
from datetime import timedelta


class PlaylistEntry(models.Model):
    """ Class for a song in playlist
    """

    class Meta:
        permissions = (
            ("delete_own_playlistentry", "Can delete a user's own playlist entry"),
        )

    song = models.ForeignKey('library.Song', null=False)
    date_created = models.DateTimeField(auto_now_add=True)

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
