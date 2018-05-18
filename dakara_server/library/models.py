from datetime import timedelta

from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator

from library.fields import UpperCaseCharField


class Song(models.Model):
    """Song object
    """
    title = models.CharField(max_length=255)
    filename = models.CharField(max_length=255)
    directory = models.CharField(max_length=255)
    duration = models.DurationField(default=timedelta(0))
    version = models.CharField(max_length=255, blank=True)
    detail = models.CharField(max_length=255, blank=True)
    detail_video = models.CharField(max_length=255, blank=True)
    tags = models.ManyToManyField('SongTag')
    artists = models.ManyToManyField('Artist')
    works = models.ManyToManyField('Work', through='SongWorkLink')
    lyrics = models.TextField(blank=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "Song '{}'".format(self.title)


class Artist(models.Model):
    """Artist object
    """
    name = models.CharField(max_length=255)

    def __str__(self):
        return "Artist '{}'".format(self.name)


class Work(models.Model):
    """Work object that uses a song

    Example: an anime, a game and so on.
    """
    title = models.CharField(max_length=255)
    subtitle = models.CharField(max_length=255, blank=True)
    work_type = models.ForeignKey('WorkType', null=True)

    def __str__(self):
        return "Work of type {} '{}'".format(
            self.work_type.get_name() if self.work_type else 'unknown',
            self.title
        )


class WorkType(models.Model):
    """Type of a work

    Example: anime, games and so on.
    """
    name = models.CharField(max_length=255)
    name_plural = models.CharField(max_length=255)
    query_name = models.CharField(max_length=255, unique=True)
    # icon_name refers to a fontawesome icon name
    icon_name = models.CharField(max_length=255, null=True)

    def __str__(self):
        return "Work type '{}'".format(self.get_name())

    def get_name(self):
        """Get the pretty name of the work type or the default one
        """
        return self.name or self.query_name


class SongWorkLink(models.Model):
    """Relation between a song and a work

    It describes the use of a song within a work.
    """
    OPENING = 'OP'
    ENDING = 'ED'
    INSERT = 'IN'
    IMAGE = 'IS'
    LINK_TYPE_CHOICES = (
        (OPENING, "Opening"),
        (ENDING, "Ending"),
        (INSERT, "Insert song"),
        (IMAGE, "Image song"),
    )

    song = models.ForeignKey(Song, on_delete=models.CASCADE)
    work = models.ForeignKey(Work, on_delete=models.CASCADE)
    link_type = models.CharField(max_length=2, choices=LINK_TYPE_CHOICES)
    link_type_number = models.IntegerField(null=True)
    episodes = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return "Use of song '{}' in '{}' as {}".format(
            self.song.title,
            self.work.title,
            self.link_type
        )


class SongTag(models.Model):
    """Song tag object
    """
    name = UpperCaseCharField(max_length=255)
    color_hue = models.IntegerField(
        null=True,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(360)])
    disabled = models.BooleanField(default=False)

    def __str__(self):
        return "Song tag '{}'".format(self.name)
