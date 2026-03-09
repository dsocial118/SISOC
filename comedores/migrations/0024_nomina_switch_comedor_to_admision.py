"""
Migración: Nómina pasa de relacionarse con Comedor a relacionarse con Admision.

Pasos:
  1. Agrega campo `admision` FK (nullable).
  2. Data migration: asigna la admisión activa con mayor ID del comedor
     correspondiente a cada registro existente. Si no hay admisión activa,
     el registro queda con admision=null.
  3. Elimina el campo `comedor`.
  4. Agrega índice explícito sobre `admision`.

Supuesto documentado: los registros de comedores sin admisión activa
quedan con admision=null (sin pérdida de datos, sin asignación incorrecta).
"""

import django.db.models.deletion
from django.db import migrations, models


def asignar_admision_a_nominas(apps, schema_editor):
    """
    Para cada Nomina con comedor asignado y sin admision, busca la admision
    activa con mayor ID de ese comedor y la asigna.
    """
    Nomina = apps.get_model("comedores", "Nomina")
    Admision = apps.get_model("admisiones", "Admision")

    comedores_ids = (
        Nomina.objects.filter(comedor__isnull=False, admision__isnull=True)
        .values_list("comedor_id", flat=True)
        .distinct()
    )

    for comedor_id in comedores_ids:
        admision = (
            Admision.objects.filter(comedor_id=comedor_id, activa=True)
            .order_by("-id")
            .first()
        )
        if admision:
            Nomina.objects.filter(
                comedor_id=comedor_id, admision__isnull=True
            ).update(admision=admision)


class Migration(migrations.Migration):

    dependencies = [
        ("admisiones", "0057_alter_archivoadmision_managers_and_more"),
        ("comedores", "0023_alter_comedor_managers_alter_nomina_managers_and_more"),
    ]

    operations = [
        # 1. Agregar campo admision (nullable para permitir data migration)
        migrations.AddField(
            model_name="nomina",
            name="admision",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="nominas",
                to="admisiones.admision",
            ),
        ),
        # 2. Data migration: asignar admision a registros existentes
        migrations.RunPython(
            asignar_admision_a_nominas,
            migrations.RunPython.noop,
        ),
        # 3. Eliminar campo comedor (MySQL elimina automáticamente su índice FK al
        #    hacer DROP COLUMN, pero el estado de Django sigue rastreando el índice
        #    nombrado creado en 0001_initial. Lo sincronizamos con SeparateDatabaseAndState.)
        migrations.RemoveField(
            model_name="nomina",
            name="comedor",
        ),
        # 4. Sincronizar estado Django: eliminar el índice de comedor del estado de
        #    migración sin operación en DB (MySQL ya lo eliminó con el DROP COLUMN).
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.RemoveIndex(
                    model_name="nomina",
                    name="comedores_n_comedor_2179d8_idx",
                ),
            ],
        ),
    ]
