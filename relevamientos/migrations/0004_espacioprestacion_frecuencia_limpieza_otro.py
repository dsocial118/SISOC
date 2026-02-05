from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("relevamientos", "0003_relevamiento_fecha_creacion"),
    ]

    operations = [
        migrations.AddField(
            model_name="espacioprestacion",
            name="frecuencia_limpieza_otro",
            field=models.CharField(
                blank=True,
                max_length=255,
                null=True,
                verbose_name="2.4.2 Si eligió 'Otra frecuencia', especificar",
            ),
        ),
    ]
