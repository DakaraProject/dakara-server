from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("playlist", "0001_initial")]
    replaces = [("playlist", "0002_karastatus")]

    operations = [
        migrations.CreateModel(
            name="KaraStatus",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        primary_key=True,
                        serialize=False,
                        auto_created=True,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        max_length=5,
                        default="stop",
                        choices=[
                            ("stop", "Stop"),
                            ("play", "Play"),
                            ("pause", "Pause"),
                        ],
                    ),
                ),
            ],
        )
    ]
