# Generated by Django 1.11.15 on 2018-12-09 10:26

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("library", "0006_work_alternative_title")]
    replaces = [("library", "0007_auto_20181209_1026")]

    operations = [
        migrations.AlterField(
            model_name="work",
            name="work_type",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="library.WorkType"
            ),
        )
    ]
