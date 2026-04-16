"""
Migración: agrega campo comedor FK nullable a Nomina.

Permite que nóminas de programas 3/4 (Abordaje comunitario) se asocien
directamente al comedor sin requerir una admisión (lógica nueva).

Relación prog 2:   nomina.admision → admision.comedor  (lógica existente)
Relación prog 3/4: nomina.comedor  → comedor            (lógica nueva)

La asignación de datos reales se realiza con el management command
`recuperar_nominas_csv` tras el deploy.
"""

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("comedores", "0028_nomina_estado_espera"),
    ]

    operations = [
        migrations.AddField(
            model_name="nomina",
            name="comedor",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="nominas_directas",
                to="comedores.comedor",
                verbose_name="Comedor (acceso directo)",
            ),
        ),
    ]
