# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2018-12-09 10:26
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [("library", "0006_workalternativetitle")]

    operations = [
        migrations.AlterField(
            model_name="work",
            name="work_type",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="library.WorkType"
            ),
        )
    ]
