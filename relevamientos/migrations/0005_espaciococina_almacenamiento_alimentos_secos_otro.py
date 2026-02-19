from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("relevamientos", "0004_espacioprestacion_frecuencia_limpieza_otro"),
    ]

    operations = [
        migrations.AddField(
            model_name="espaciococina",
            name="almacenamiento_alimentos_secos_otro",
            field=models.CharField(
                blank=True,
                max_length=255,
                null=True,
                verbose_name="2.2.2.1 Si respondió 'No', especificar dónde almacenan",
            ),
        ),
    ]
