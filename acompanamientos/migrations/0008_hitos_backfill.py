"""
Data migration (dos pasos):

1. Crea Acompanamiento para las admisiones con enviado_acompaniamiento=True que
   no tuvieran uno. Esto cubre el gap de admisiones disponibilizadas entre la
   migración 0005 y el fix del bug en _procesar_post_disponibilizar_acomp.

2. Crea Hitos para cada Acompanamiento que no tenga uno asociado. Cubre el gap
   de los Acompañamientos creados por la migración 0005 (datos históricos) para
   los cuales no existía un Hitos previo.
"""

from django.db import migrations


def crear_acompaniamientos_y_hitos_faltantes(apps, schema_editor):
    Admision = apps.get_model("admisiones", "Admision")
    Acompanamiento = apps.get_model("acompanamientos", "Acompanamiento")
    Hitos = apps.get_model("acompanamientos", "Hitos")

    # Paso 1: crear Acompanamiento para admisiones enviadas sin uno
    for admision in Admision.objects.filter(
        enviado_acompaniamiento=True, acompanamiento__isnull=True
    ).order_by("id"):
        nro = admision.numero_convenio or (
            str(admision.convenio_numero) if admision.convenio_numero else ""
        )
        Acompanamiento.objects.get_or_create(
            admision=admision,
            defaults={"nro_convenio": nro},
        )

    # Paso 2: crear Hitos para cada Acompanamiento sin ellos
    for acompanamiento in Acompanamiento.objects.filter(hitos__isnull=True):
        Hitos.objects.create(acompanamiento=acompanamiento)


def revertir_backfill(apps, schema_editor):
    # No hay forma segura de deshacer esto sin saber cuáles fueron creados aquí.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("acompanamientos", "0007_hitos_cleanup_comedor"),
    ]

    operations = [
        migrations.RunPython(
            crear_acompaniamientos_y_hitos_faltantes,
            revertir_backfill,
        ),
    ]
