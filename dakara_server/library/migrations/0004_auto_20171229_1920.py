# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [("library", "0003_auto_20171229_1841")]

    operations = [
        migrations.AlterField(
            model_name="songtag",
            name="color_hue",
            field=models.IntegerField(
                validators=[
                    django.core.validators.MinValueValidator(0),
                    django.core.validators.MaxValueValidator(360),
                ],
                null=True,
            ),
        )
    ]
