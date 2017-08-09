# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0008_auto_20170122_1346'),
    ]

    operations = [
        migrations.RenameField(
            model_name='song',
            old_name='file_path',
            new_name='filename',
        ),
        migrations.AddField(
            model_name='song',
            name='directory',
            field=models.CharField(max_length=255, default=''),
            preserve_default=False,
        ),
    ]
