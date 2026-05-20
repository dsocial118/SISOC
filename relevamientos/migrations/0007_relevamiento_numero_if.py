from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        (
            "relevamientos",
            "0006_alter_relevamiento_managers_relevamiento_deleted_at_and_more",
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
