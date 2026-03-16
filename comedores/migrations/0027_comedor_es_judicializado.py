from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("comedores", "0026_remove_nomina_comedores_n_admisio_b94ec3_idx"),
    ]

    operations = [
        migrations.AddField(
            model_name="comedor",
            name="es_judicializado",
            field=models.BooleanField(
                blank=True,
                null=True,
                verbose_name="¿Es judicializado?",
            ),
        ),
    ]
