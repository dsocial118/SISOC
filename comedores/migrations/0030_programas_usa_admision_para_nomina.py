"""
Marca qué programas siguen el flujo de admisión para la nómina.

Los programas 3 y 4 quedan como nómina directa por comedor, por eso el flag
se inicializa en False para ambos y en True para el resto por defecto.
"""

from django.db import migrations, models


def backfill_programas_sin_admision_para_nomina(apps, schema_editor):
    programas_model = apps.get_model("comedores", "Programas")
    programas_model.objects.filter(id__in=[3, 4]).update(
        usa_admision_para_nomina=False
    )


class Migration(migrations.Migration):

    dependencies = [
        ("comedores", "0029_nomina_comedor_directo"),
    ]

    operations = [
        migrations.AddField(
            model_name="programas",
            name="usa_admision_para_nomina",
            field=models.BooleanField(
                default=True,
                help_text=(
                    "Cuando es False, la nómina del comedor se gestiona de forma "
                    "directa sin depender de admisiones."
                ),
                verbose_name="¿Usa admisión para nómina?",
            ),
        ),
        migrations.RunPython(
            backfill_programas_sin_admision_para_nomina,
            migrations.RunPython.noop,
        ),
    ]
