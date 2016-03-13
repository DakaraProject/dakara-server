# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime
import library.fields


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0002_song_duration'),
    ]

    operations = [
        migrations.AlterField(
            model_name='song',
            name='duration',
            field=library.fields.SafeDurationField(default=datetime.timedelta(0)),
        ),
    ]
