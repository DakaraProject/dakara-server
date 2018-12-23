# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("playlist", "0003_auto_20180402_1443")]

    operations = [
        migrations.AddField(
            model_name="playlistentry",
            name="date_played",
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name="playlistentry",
            name="was_played",
            field=models.BooleanField(default=False),
        ),
    ]
