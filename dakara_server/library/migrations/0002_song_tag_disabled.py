from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("library", "0001_initial")]
    replaces = [("library", "0002_songtag_disabled")]

    operations = [
        migrations.AddField(
            model_name="songtag",
            name="disabled",
            field=models.BooleanField(default=False),
        )
    ]
