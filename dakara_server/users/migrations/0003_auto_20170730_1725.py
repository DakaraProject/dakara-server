# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_auto_20170730_1432'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dakarauser',
            name='playlist_permission_level',
            field=models.CharField(max_length=1, null=True, choices=[('p', 'Player'), ('u', 'User'), ('m', 'Manager')]),
        ),
    ]
