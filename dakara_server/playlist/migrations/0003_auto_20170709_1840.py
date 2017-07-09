# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('playlist', '0002_auto_20170702_1549'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='playlistentry',
            options={},
        ),
        migrations.AddField(
            model_name='playlistentry',
            name='owner',
            field=models.ForeignKey(default=1, to=settings.AUTH_USER_MODEL),
            preserve_default=False,
        ),
    ]
