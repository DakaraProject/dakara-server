# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='dakarauser',
            name='library_permission_level',
            field=models.CharField(max_length=1, null=True, choices=[('u', 'User'), ('m', 'Manager')]),
        ),
        migrations.AddField(
            model_name='dakarauser',
            name='playlist_permission_level',
            field=models.CharField(max_length=1, null=True, choices=[('p', 'player'), ('u', 'User'), ('m', 'Manager')]),
        ),
        migrations.AddField(
            model_name='dakarauser',
            name='users_permission_level',
            field=models.CharField(max_length=1, null=True, choices=[('u', 'User'), ('m', 'Manager')]),
        ),
    ]
