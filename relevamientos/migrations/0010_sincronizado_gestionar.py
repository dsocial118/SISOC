from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("relevamientos", "0009_primerseguimiento_gestionar_id"),
    ]

    operations = [
        migrations.AddField(
            model_name="relevamiento",
            name="sincronizado_gestionar",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="primerseguimiento",
            name="sincronizado_gestionar",
            field=models.BooleanField(default=False),
        ),
    ]
