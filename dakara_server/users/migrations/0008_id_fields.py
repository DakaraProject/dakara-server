# Generated by Django 3.2.12 on 2022-04-13 17:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0007_dakara_user_case_insensitive_fields"),
    ]

    operations = [
        migrations.AlterField(
            model_name="dakarauser",
            name="first_name",
            field=models.CharField(
                blank=True, max_length=150, verbose_name="first name"
            ),
        ),
        migrations.AlterField(
            model_name="dakarauser",
            name="id",
            field=models.BigAutoField(
                auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
            ),
        ),
        migrations.AlterField(
            model_name="dakarauser",
            name="playlist_permission_level",
            field=models.CharField(
                choices=[("u", "User"), ("m", "Manager")],
                default="u",
                max_length=1,
                null=True,
            ),
        ),
    ]
