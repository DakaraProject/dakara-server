# Generated by Django 2.2.11 on 2020-03-29 13:03

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("library", "0008_auto_20190609_0705"),
    ]

    operations = [
        migrations.AlterField(
            model_name="songworklink",
            name="song",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="library.Song"
            ),
        ),
        migrations.AlterField(
            model_name="songworklink",
            name="work",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="library.Work"
            ),
        ),
    ]
