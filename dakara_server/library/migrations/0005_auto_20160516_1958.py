# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0004_auto_20160424_1604'),
    ]

    operations = [
        migrations.CreateModel(
            name='WorkType',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('icon_name', models.CharField(null=True, max_length=255)),
            ],
        ),
        migrations.AddField(
            model_name='work',
            name='work_type',
            field=models.ForeignKey(null=True, to='library.WorkType'),
        ),
    ]
