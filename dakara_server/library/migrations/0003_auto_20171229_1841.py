# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("library", "0002_songtag_disabled")]

    operations = [
        migrations.RenameField(
            model_name="songtag", old_name="color_id", new_name="color_hue"
        )
    ]
