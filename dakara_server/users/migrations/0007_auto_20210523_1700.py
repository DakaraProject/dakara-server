# Generated by Django 2.2.17 on 2021-05-23 17:00

import django.contrib.auth.models
from django.db import migrations
import users.fields


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0006_auto_20201128_0833"),
    ]

    operations = [
        migrations.AlterModelManagers(
            name="dakarauser",
            managers=[("objects", django.contrib.auth.models.UserManager())],
        ),
        migrations.AlterField(
            model_name="dakarauser",
            name="email",
            field=users.fields.CaseInsensitiveEmailField(
                max_length=254, unique=True, verbose_name="email address"
            ),
        ),
        migrations.AlterField(
            model_name="dakarauser",
            name="username",
            field=users.fields.CaseInsensitiveCharField(
                help_text="Required. 150 characters or fewer. "
                "Letters, digits and @/./+/-/_ only.",
                max_length=150,
                unique=True,
                verbose_name="username",
            ),
        ),
    ]
