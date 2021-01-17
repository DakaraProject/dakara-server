from datetime import timedelta

from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator


class Song(models.Model):
    """Song object
    """

    title = models.CharField(max_length=255)
    filename = models.CharField(max_length=255)
    directory = models.CharField(max_length=255, blank=True)
    duration = models.DurationField(default=timedelta(0))
    version = models.CharField(max_length=255, blank=True)
    detail = models.CharField(max_length=255, blank=True)
    detail_video = models.CharField(max_length=255, blank=True)
    tags = models.ManyToManyField("SongTag")
    artists = models.ManyToManyField("Artist")
    works = models.ManyToManyField("Work", through="SongWorkLink")
    lyrics = models.TextField(blank=True)
    has_instrumental = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class Artist(models.Model):
    """Artist object
    """

    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Work(models.Model):
    """Work object that uses a song

    Example: an anime, a game and so on.
    """

    title = models.CharField(max_length=255)
    subtitle = models.CharField(max_length=255, blank=True)
    work_type = models.ForeignKey("WorkType", on_delete=models.CASCADE)

    def __str__(self):
        return "{} ({})".format(self.title, self.work_type)


class WorkAlternativeTitle(models.Model):
    """Alternative title of a work
    """

    title = models.CharField(max_length=255)
    work = models.ForeignKey(
        Work,
        on_delete=models.CASCADE,
        related_name="alternative_titles",
        related_query_name="alternative_title",
    )

    def __str__(self):
        return "{} [{}]".format(self.title, self.work)


class WorkType(models.Model):
    """Type of a work

    Example: anime, games and so on.
    """

    query_name = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    name_plural = models.CharField(max_length=255)
    # icon_name refers to a fontawesome icon name
    icon_name = models.CharField(max_length=255, null=True)

    def __str__(self):
        return self.name or self.query_name


class SongWorkLink(models.Model):
    """Relation between a song and a work

    It describes the use of a song within a work.
    """

    OPENING = "OP"
    ENDING = "ED"
    INSERT = "IN"
    IMAGE = "IS"
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
        return "{} <{}> {}".format(self.song, self.link_type, self.work)

    def __hash__(self):
        fields = frozenset(
            (self.song.pk, self.work.pk, self.link_type, self.link_type_number)
        )
        return hash(fields)

    def __eq__(self, other):
        return self.__hash__() == other.__hash__()


class SongTag(models.Model):
    """Song tag object
    """

    name = models.CharField(max_length=255, unique=True)
    color_hue = models.IntegerField(
        null=True, validators=[MinValueValidator(0), MaxValueValidator(360)]
    )
    disabled = models.BooleanField(default=False)

    def __str__(self):
        return self.name
