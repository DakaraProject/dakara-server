from django.db import models

class PlaylistEntry(models.Model):
    """ Class for a song in playlist
    """
    song = models.ForeignKey('library.Song', null=False)
    date_created = models.DateTimeField(auto_now_add=True)

class Player(models.Model):
    """ Class for status recieved from the player
    """

    playlist_entry = models.ForeignKey('PlaylistEntry', null=True)
    timing = models.DurationField(null=True)
    paused  = models.BooleanField(default=False)


class PlayerCommand(models.Model):
    """ Class for user commands to the player
    """

    pause = models.BooleanField(default=False)
    skip = models.BooleanField(default=False)
