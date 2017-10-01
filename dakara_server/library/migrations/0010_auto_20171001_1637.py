# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0009_auto_20170809_1658'),
    ]

    operations = [
        migrations.AddField(
            model_name='song',
            name='lyrics',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='song',
            name='duration',
            field=models.DurationField(default=datetime.timedelta(0)),
        ),
    ]
