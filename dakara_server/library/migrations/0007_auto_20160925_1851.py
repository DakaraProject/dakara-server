# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import library.models


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0006_auto_20160523_1810'),
    ]

    operations = [
        migrations.AddField(
            model_name='worktype',
            name='query_name',
            field=models.CharField(default='empty', max_length=255),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='songtag',
            name='name',
            field=library.models.UpperCaseCharField(max_length=255),
        ),
    ]
