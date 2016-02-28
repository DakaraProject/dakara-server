from django.db import models
from datetime import timedelta


class Song(models.Model):
    """ Class for songs
    """
    title = models.CharField(max_length=255)
    file_path = models.CharField(max_length=255)
    duration = models.DurationField(default=timedelta(0))
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.title)
