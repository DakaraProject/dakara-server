# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime


class Migration(migrations.Migration):

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Artist",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                ("name", models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name="Song",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                ("title", models.CharField(max_length=255)),
                ("filename", models.CharField(max_length=255)),
                ("directory", models.CharField(max_length=255)),
                ("duration", models.DurationField(default=datetime.timedelta(0))),
                ("version", models.CharField(blank=True, max_length=255)),
                ("detail", models.CharField(blank=True, max_length=255)),
                ("detail_video", models.CharField(blank=True, max_length=255)),
                ("lyrics", models.TextField(blank=True)),
                ("date_created", models.DateTimeField(auto_now_add=True)),
                ("date_updated", models.DateTimeField(auto_now=True)),
                ("artists", models.ManyToManyField(to="library.Artist")),
            ],
        ),
        migrations.CreateModel(
            name="SongTag",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                ("name", models.CharField(max_length=255)),
                ("color_id", models.IntegerField(null=True)),
            ],
        ),
        migrations.CreateModel(
            name="SongWorkLink",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                (
                    "link_type",
                    models.CharField(
                        max_length=2,
                        choices=[
                            ("OP", "Opening"),
                            ("ED", "Ending"),
                            ("IN", "Insert song"),
                            ("IS", "Image somg"),
                        ],
                    ),
                ),
                ("link_type_number", models.IntegerField(null=True)),
                ("episodes", models.CharField(blank=True, max_length=255)),
                (
                    "song",
                    models.ForeignKey(to="library.Song", on_delete=models.DO_NOTHING),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Work",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                ("title", models.CharField(max_length=255)),
                ("subtitle", models.CharField(blank=True, max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name="WorkType",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                ("name", models.CharField(max_length=255)),
                ("name_plural", models.CharField(max_length=255)),
                ("query_name", models.CharField(max_length=255, unique=True)),
                ("icon_name", models.CharField(null=True, max_length=255)),
            ],
        ),
        migrations.AddField(
            model_name="work",
            name="work_type",
            field=models.ForeignKey(
                null=True, to="library.WorkType", on_delete=models.DO_NOTHING
            ),
        ),
        migrations.AddField(
            model_name="songworklink",
            name="work",
            field=models.ForeignKey(to="library.Work", on_delete=models.DO_NOTHING),
        ),
        migrations.AddField(
            model_name="song",
            name="tags",
            field=models.ManyToManyField(to="library.SongTag"),
        ),
        migrations.AddField(
            model_name="song",
            name="works",
            field=models.ManyToManyField(
                through="library.SongWorkLink", to="library.Work"
            ),
        ),
    ]
