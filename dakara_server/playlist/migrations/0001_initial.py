# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Player',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timing', models.DurationField(null=True)),
                ('pause_requested', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='PlaylistEntry',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('song', models.ForeignKey(to='library.Song')),
            ],
        ),
        migrations.AddField(
            model_name='player',
            name='playlist_entry',
            field=models.ForeignKey(to='playlist.PlaylistEntry', null=True),
        ),
        migrations.AddField(
            model_name='player',
            name='skip_requested',
            field=models.ForeignKey(to='playlist.PlaylistEntry', related_name='skip', null=True),
        ),
    ]
