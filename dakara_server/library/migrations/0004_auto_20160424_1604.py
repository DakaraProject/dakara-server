# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0003_auto_20160313_1822'),
    ]

    operations = [
        migrations.CreateModel(
            name='Artist',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='SongWorkLink',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('link_type_number', models.IntegerField(null=True)),
                ('link_type', models.CharField(max_length=2, choices=[('OP', 'Opening'), ('ED', 'Ending'), ('IN', 'Insert song'), ('IS', 'Image somg')])),
            ],
        ),
        migrations.CreateModel(
            name='Work',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('title', models.CharField(max_length=255)),
                ('subtitle', models.CharField(max_length=255, blank=True)),
            ],
        ),
        migrations.AddField(
            model_name='song',
            name='detail',
            field=models.CharField(max_length=255, blank=True),
        ),
        migrations.AddField(
            model_name='songworklink',
            name='song',
            field=models.ForeignKey(to='library.Song'),
        ),
        migrations.AddField(
            model_name='songworklink',
            name='work',
            field=models.ForeignKey(to='library.Work'),
        ),
        migrations.AddField(
            model_name='song',
            name='artists',
            field=models.ManyToManyField(to='library.Artist'),
        ),
        migrations.AddField(
            model_name='song',
            name='works',
            field=models.ManyToManyField(through='library.SongWorkLink', to='library.Work'),
        ),
    ]
