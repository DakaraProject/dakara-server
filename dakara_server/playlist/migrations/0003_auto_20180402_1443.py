# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('playlist', '0002_karastatus'),
    ]

    operations = [
        migrations.AlterField(
            model_name='karastatus',
            name='status',
            field=models.CharField(default='play', max_length=5, choices=[('stop', 'Stop'), ('play', 'Play'), ('pause', 'Pause')]),
        ),
    ]
