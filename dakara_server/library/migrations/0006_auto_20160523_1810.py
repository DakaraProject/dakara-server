# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0005_auto_20160516_1958'),
    ]

    operations = [
        migrations.CreateModel(
            name='SongTag',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('color_id', models.IntegerField(null=True)),
            ],
        ),
        migrations.AddField(
            model_name='song',
            name='tags',
            field=models.ManyToManyField(to='library.SongTag'),
        ),
    ]
