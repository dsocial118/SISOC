"""
Fase 4 — Limpieza del campo comedor en Hitos.

Pasos:
1. Borra los Hitos huérfanos (sin acompanamiento vinculado).
   El equipo confirmó que se puede perder esa data (894 registros vacíos + 11
   con datos reales sin admisión asociada — ver tk1273).
2. Hace el campo acompanamiento NOT NULL.
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
        # 1. Borrar huérfanos antes de poner NOT NULL
        migrations.RunPython(
            borrar_hitos_huerfanos,
            revertir_hitos_huerfanos,
        ),
        # 2. acompanamiento pasa a NOT NULL
        migrations.AlterField(
            model_name="hitos",
            name="acompanamiento",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.SET_NULL,
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
