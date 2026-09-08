# pylint: disable=invalid-name

from django.db import migrations


LEGACY_CATEGORY = "comprobantes"
ALIMENTARIO_CATEGORY = "comprobantes_alimentario"


def reconciliar_comprobantes_legacy(apps, schema_editor):
    """Mueve todas las filas legacy, incluidas las dadas de baja lógica."""
    documento_model = apps.get_model("rendicioncuentasmensual", "DocumentacionAdjunta")
    database = schema_editor.connection.alias
    documento_model.all_objects.using(database).filter(
        categoria=LEGACY_CATEGORY
    ).update(categoria=ALIMENTARIO_CATEGORY)


class Migration(migrations.Migration):
    dependencies = [
        ("rendicioncuentasmensual", "0018_stage_permissions"),
    ]

    operations = [
        migrations.RunPython(
            reconciliar_comprobantes_legacy,
            migrations.RunPython.noop,
            atomic=True,
        ),
    ]
