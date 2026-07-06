from django.db import migrations


ESPACIOS_COMUNITARIOS_SLUGS = [
    "perfilamiento-de-espacios-comunitarios",
    "seguimiento-espacios-comunitatios",
    "coordinadores-alimentar-comunidad",
    "comedores-interno",
]


def backfill_espacios_comunitarios(apps, schema_editor):
    """Agrupa los tableros de Espacios Comunitarios.

    Solo toca filas sin ``grupo_menu`` para no pisar ediciones manuales.
    """
    Tablero = apps.get_model("dashboard", "Tablero")
    Tablero.objects.filter(slug__in=ESPACIOS_COMUNITARIOS_SLUGS).filter(
        grupo_menu=""
    ).update(grupo_menu="Espacios Comunitarios")


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("dashboard", "0002_tablero_grupo_menu"),
    ]

    operations = [
        migrations.RunPython(backfill_espacios_comunitarios, noop_reverse),
    ]
