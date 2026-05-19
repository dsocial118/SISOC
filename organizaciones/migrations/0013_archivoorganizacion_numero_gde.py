from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("organizaciones", "0012_documentacion_organizacion"),
    ]

    operations = [
        migrations.AddField(
            model_name="archivoorganizacion",
            name="numero_gde",
            field=models.CharField(
                "Numero de GDE",
                max_length=50,
                blank=True,
                null=True,
            ),
        ),
    ]
