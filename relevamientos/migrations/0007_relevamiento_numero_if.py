from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        (
            "relevamientos",
            "0001_squashed_0006",
        ),
    ]

    operations = [
        migrations.AddField(
            model_name="relevamiento",
            name="numero_if",
            field=models.CharField(
                "Número de IF",
                blank=True,
                max_length=255,
                null=True,
            ),
        ),
    ]
