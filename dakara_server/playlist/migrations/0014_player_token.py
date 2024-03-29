# Generated by Django 2.2.17 on 2022-01-15 11:25

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("playlist", "0013_player"),
    ]

    operations = [
        migrations.CreateModel(
            name="PlayerToken",
            fields=[
                (
                    "karaoke",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        primary_key=True,
                        related_name="player_token",
                        serialize=False,
                        to="playlist.Karaoke",
                    ),
                ),
                ("key", models.CharField(editable=False, max_length=40, unique=True)),
            ],
        ),
    ]
