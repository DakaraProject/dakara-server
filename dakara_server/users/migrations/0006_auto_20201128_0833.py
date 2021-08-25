# Generated by Django 2.2.13 on 2020-11-28 08:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0005_auto_20201018_1106"),
    ]

    operations = [
        migrations.AlterField(
            model_name="dakarauser",
            name="playlist_permission_level",
            field=models.CharField(
                choices=[("p", "Player"), ("u", "User"), ("m", "Manager")],
                default="u",
                max_length=1,
                null=True,
            ),
        ),
    ]