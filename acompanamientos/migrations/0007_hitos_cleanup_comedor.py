"""
Fase 4 — Limpieza del campo comedor en Hitos.

Pasos:
1. Borra los Hitos huérfanos (sin acompanamiento vinculado).
   El equipo confirmó que se puede perder esa data (894 registros vacíos + 11
   con datos reales sin admisión asociada — ver tk1273).
2. Conserva el campo acompanamiento nullable para permitir `SET_NULL` durante
   la transición y reflejar el estado real del modelo.
3. Elimina el campo comedor de Hitos.
"""

from django.db import migrations, models
import django.db.models.deletion


def borrar_hitos_huerfanos(apps, schema_editor):
    Hitos = apps.get_model("acompanamientos", "Hitos")
    Hitos.objects.filter(acompanamiento__isnull=True).delete()


def revertir_hitos_huerfanos(apps, schema_editor):
    # No se pueden restaurar los registros borrados.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("acompanamientos", "0006_alter_acompanamiento_id"),
    ]

    operations = [
        # 1. Borrar huérfanos antes de remover `comedor`
        migrations.RunPython(
            borrar_hitos_huerfanos,
            revertir_hitos_huerfanos,
        ),
        # 2. acompanamiento se mantiene nullable; la operación documenta el
        #    schema final y evita drift entre migración y modelo.
        migrations.AlterField(
            model_name="hitos",
            name="acompanamiento",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.SET_NULL,
                blank=True,
                null=True,
                related_name="hitos",
                to="acompanamientos.acompanamiento",
            ),
        ),
        # 3. Eliminar campo comedor de Hitos
        migrations.RemoveField(
            model_name="hitos",
            name="comedor",
        ),
    ]
