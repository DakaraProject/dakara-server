# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('playlist', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='playlistentry',
            options={'permissions': (('delete_own_playlistentry', "Can delete a user's own playlist entry"),)},
        ),
    ]
