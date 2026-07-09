# Generated manually in FAST mode.

from django.db import migrations


INFORME_TECNICO_REPAIR_COMIDAS = ("desayuno", "almuerzo", "merienda", "cena")
INFORME_TECNICO_REPAIR_DIAS = (
    "lunes",
    "martes",
    "miercoles",
    "jueves",
    "viernes",
    "sabado",
    "domingo",
)
INFORME_TECNICO_REPAIR_FIELDS = (
    *(
        f"aprobadas_ultimo_convenio_{comida}_{dia}"
        for comida in INFORME_TECNICO_REPAIR_COMIDAS
        for dia in INFORME_TECNICO_REPAIR_DIAS
    ),
    "observaciones_subsanacion",
)


def repair_informetecnico_missing_columns(apps, schema_editor):
    InformeTecnico = apps.get_model("admisiones", "InformeTecnico")
    table_name = InformeTecnico._meta.db_table
    with schema_editor.connection.cursor() as cursor:
        existing_columns = {
            column.name
            for column in schema_editor.connection.introspection.get_table_description(
                cursor,
                table_name,
            )
        }
    for field_name in INFORME_TECNICO_REPAIR_FIELDS:
        if field_name in existing_columns:
            continue
        field = InformeTecnico._meta.get_field(field_name)
        schema_editor.add_field(InformeTecnico, field)
        existing_columns.add(field_name)


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("admisiones", "0065_admision_vigente_pwa"),
    ]

    operations = [
        migrations.RunPython(
            repair_informetecnico_missing_columns,
            migrations.RunPython.noop,
        ),
    ]
