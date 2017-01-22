# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0007_auto_20160925_1851'),
    ]

    operations = [
        migrations.AddField(
            model_name='song',
            name='detail_video',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='song',
            name='version',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='songworklink',
            name='episodes',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='worktype',
            name='query_name',
            field=models.CharField(max_length=255, unique=True),
        ),
    ]
