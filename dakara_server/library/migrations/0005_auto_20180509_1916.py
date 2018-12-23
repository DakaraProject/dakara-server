# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("library", "0004_auto_20171229_1920")]

    operations = [
        migrations.AlterField(
            model_name="songworklink",
            name="link_type",
            field=models.CharField(
                max_length=2,
                choices=[
                    ("OP", "Opening"),
                    ("ED", "Ending"),
                    ("IN", "Insert song"),
                    ("IS", "Image song"),
                ],
            ),
        )
    ]
