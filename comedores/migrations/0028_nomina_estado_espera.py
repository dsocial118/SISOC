"""
Migración: renombra el valor "pendiente" → "espera" en Nomina.estado
y actualiza choices + default del campo.
"""

from django.db import migrations, models


def pendiente_a_espera(apps, schema_editor):
    Nomina = apps.get_model("comedores", "Nomina")
    Nomina.objects.filter(estado="pendiente").update(estado="espera")


def espera_a_pendiente(apps, schema_editor):
    Nomina = apps.get_model("comedores", "Nomina")
    Nomina.objects.filter(estado="espera").update(estado="pendiente")


class Migration(migrations.Migration):

    dependencies = [
        ("comedores", "0027_comedor_es_judicializado"),
    ]

    operations = [
        migrations.RunPython(pendiente_a_espera, espera_a_pendiente),
        migrations.AlterField(
            model_name="nomina",
            name="estado",
            field=models.CharField(
                choices=[
                    ("activo", "Activo"),
                    ("espera", "En espera"),
                    ("baja", "Baja"),
                ],
                default="activo",
                max_length=20,
            ),
        ),
    ]
