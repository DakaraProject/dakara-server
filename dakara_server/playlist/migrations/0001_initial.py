from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("library", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="PlaylistEntry",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        primary_key=True,
                        auto_created=True,
                        serialize=False,
                    ),
                ),
                ("date_created", models.DateTimeField(auto_now_add=True)),
                (
                    "owner",
                    models.ForeignKey(
                        to=settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING
                    ),
                ),
                (
                    "song",
                    models.ForeignKey(to="library.Song", on_delete=models.DO_NOTHING),
                ),
            ],
        )
    ]
