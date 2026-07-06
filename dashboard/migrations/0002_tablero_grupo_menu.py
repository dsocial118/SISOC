from django.db import migrations, models


def backfill_grupo_menu(apps, schema_editor):
    """Agrupa los tableros existentes por programa según su nombre.

    Solo toca filas sin ``grupo_menu`` para no pisar ediciones manuales.
    """
    Tablero = apps.get_model("dashboard", "Tablero")
    datacalle = Tablero.objects.filter(nombre__startswith="DataCalle").exclude(
        grupo_menu="DataCalle"
    )
    datacalle.filter(grupo_menu="").update(grupo_menu="DataCalle")
    Tablero.objects.filter(nombre__in=["Aduana", "Aduana Ejecutivo"]).filter(
        grupo_menu=""
    ).update(grupo_menu="Aduana")


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("dashboard", "0001_squashed_0003"),
    ]

    operations = [
        migrations.AddField(
            model_name="tablero",
            name="grupo_menu",
            field=models.CharField(
                blank=True,
                default="",
                help_text=(
                    "Nombre del programa/grupo bajo el que se agrupa en el menú "
                    "de Tableros. Vacío = aparece como enlace directo (sin "
                    "submenú). No confundir con los grupos de permisos."
                ),
                max_length=255,
            ),
        ),
        migrations.RunPython(backfill_grupo_menu, noop_reverse),
    ]
