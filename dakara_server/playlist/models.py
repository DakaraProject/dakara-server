from django.db import models

class PlaylistEntry(models.Model):
    """ Class for a song in playlist
    """
    song = models.ForeignKey('Song', null=False)
    date_created = models.DateTimeField(auto_now_add=True)

class Player(models.Model):
    """ Class for the playlist player
    """
    # recieved from the player
    playlist_entry = models.ForeignKey('PlaylistEntry', null=True)
    timing = models.DurationField(null=True)

    # requested by the server
    is_pause_requested = models.BooleanField(default=False)
    skip_requested = models.ForeignKey('PlaylistEntry', null=True)
