from django.db import models
from datetime import timedelta
from library.fields import SafeDurationField


class Song(models.Model):
    """ Class for songs
    """
    title = models.CharField(max_length=255)
    filename = models.CharField(max_length=255)
    directory = models.CharField(max_length=255)
    duration = SafeDurationField(default=timedelta(0))
    version = models.CharField(max_length=255, blank=True)
    detail = models.CharField(max_length=255, blank=True)
    detail_video = models.CharField(max_length=255, blank=True)
    tags = models.ManyToManyField('SongTag')
    artists = models.ManyToManyField('Artist')
    works = models.ManyToManyField('Work', through='SongWorkLink')
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.title)


class Artist(models.Model):
    """ Class for artists
    """
    name = models.CharField(max_length=255)

    def __str__(self):
        return str(self.name)


class Work(models.Model):
    """ Class for anime, games and so on that use songs
    """
    title = models.CharField(max_length=255)
    subtitle = models.CharField(max_length=255, blank=True)
    work_type = models.ForeignKey('WorkType', null=True)

    def __str__(self):
        return str(self.title)


class WorkType(models.Model):
    """ Class for the type of a work: anime, games and so on 
    """
    name = models.CharField(max_length=255)
    query_name = models.CharField(max_length=255, unique=True)
    # icon_name refers to a fontawesome icon name
    icon_name = models.CharField(max_length=255, null=True)

    def __str__(self):
        return str(self.name)


class SongWorkLink(models.Model):
    """ Class to describe the use of a song in a work
    """
    OPENING = 'OP'
    ENDING = 'ED'
    INSERT = 'IN'
    IMAGE = 'IS'
    LINK_TYPE_CHOICES = (
            (OPENING, "Opening"),
            (ENDING, "Ending"),
            (INSERT, "Insert song"),
            (IMAGE, "Image somg"),
            )

    song = models.ForeignKey(Song, on_delete=models.CASCADE)
    work = models.ForeignKey(Work, on_delete=models.CASCADE)
    link_type = models.CharField(max_length=2, choices=LINK_TYPE_CHOICES)
    link_type_number = models.IntegerField(null=True)
    episodes = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return str(self.work.title) + ' ' + str(self.link_type) + \
            (' ' + str(self.link_type_number) if self.link_type_number else '')


class UpperCaseCharField(models.CharField):
    """ Override a Django Model Field and make it upper-case as of Django 1.8
        http://stackoverflow.com/a/33354171
    """

    def __init__(self, *args, **kwargs):
        super(UpperCaseCharField, self).__init__(*args, **kwargs)

    def pre_save(self, model_instance, add):
        value = getattr(model_instance, self.attname, None)
        if value:
            value = value.upper()
            setattr(model_instance, self.attname, value)
            return value
        else:
            return super(UpperCaseCharField, self).pre_save(model_instance, add)


class SongTag(models.Model):
    """ Class to describe song tags
    """
    name = UpperCaseCharField(max_length=255)
    color_id = models.IntegerField(null=True)

    def __str__(self):
        return str(self.name)
