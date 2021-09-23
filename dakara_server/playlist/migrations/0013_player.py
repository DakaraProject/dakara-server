# Generated by Django 2.2.17 on 2021-09-23 10:42

import datetime

from django.db import migrations, models

import internal.cache_model


class Migration(migrations.Migration):

    dependencies = [
        ("playlist", "0012_playlist_entry_use_instrumental"),
    ]

    operations = [
        migrations.CreateModel(
            name="Player",
            fields=[
                (
                    "karaoke",
                    internal.cache_model.OneToOneField(
                        on_delete=internal.cache_model.CASCADE,
                        primary_key=True,
                        serialize=False,
                        to="playlist.Karaoke",
                    ),
                ),
                ("timing", models.DurationField(default=datetime.timedelta(0))),
                ("paused", models.BooleanField(default=False)),
                ("in_transition", models.BooleanField(default=False)),
                ("date", models.DateTimeField(auto_now=True)),
            ],
            options={
                "abstract": False,
                "managed": False,
            },
        ),
    ]
