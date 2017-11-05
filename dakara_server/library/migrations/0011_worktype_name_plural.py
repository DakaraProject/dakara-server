# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0010_auto_20171001_1637'),
    ]

    operations = [
        migrations.AddField(
            model_name='worktype',
            name='name_plural',
            field=models.CharField(default='', max_length=255),
            preserve_default=False,
        ),
    ]
