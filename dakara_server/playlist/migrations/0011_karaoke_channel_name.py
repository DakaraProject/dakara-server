# Generated by Django 2.2.11 on 2020-04-05 07:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("playlist", "0010_karaoke_fk_cascade"),
    ]

    operations = [
        migrations.AddField(
            model_name="karaoke",
            name="channel_name",
            field=models.CharField(max_length=255, null=True),
        ),
    ]
