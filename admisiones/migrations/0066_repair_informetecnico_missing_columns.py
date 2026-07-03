# Generated manually in FAST mode.

from django.db import migrations


INFORME_TECNICO_REPAIR_FIELDS = (
    "aprobadas_ultimo_convenio_desayuno_lunes",
    "aprobadas_ultimo_convenio_desayuno_martes",
    "aprobadas_ultimo_convenio_desayuno_miercoles",
    "aprobadas_ultimo_convenio_desayuno_jueves",
    "aprobadas_ultimo_convenio_desayuno_viernes",
    "aprobadas_ultimo_convenio_desayuno_sabado",
    "aprobadas_ultimo_convenio_desayuno_domingo",
    "aprobadas_ultimo_convenio_almuerzo_lunes",
    "aprobadas_ultimo_convenio_almuerzo_martes",
    "aprobadas_ultimo_convenio_almuerzo_miercoles",
    "aprobadas_ultimo_convenio_almuerzo_jueves",
    "aprobadas_ultimo_convenio_almuerzo_viernes",
    "aprobadas_ultimo_convenio_almuerzo_sabado",
    "aprobadas_ultimo_convenio_almuerzo_domingo",
    "aprobadas_ultimo_convenio_merienda_lunes",
    "aprobadas_ultimo_convenio_merienda_martes",
    "aprobadas_ultimo_convenio_merienda_miercoles",
    "aprobadas_ultimo_convenio_merienda_jueves",
    "aprobadas_ultimo_convenio_merienda_viernes",
    "aprobadas_ultimo_convenio_merienda_sabado",
    "aprobadas_ultimo_convenio_merienda_domingo",
    "aprobadas_ultimo_convenio_cena_lunes",
    "aprobadas_ultimo_convenio_cena_martes",
    "aprobadas_ultimo_convenio_cena_miercoles",
    "aprobadas_ultimo_convenio_cena_jueves",
    "aprobadas_ultimo_convenio_cena_viernes",
    "aprobadas_ultimo_convenio_cena_sabado",
    "aprobadas_ultimo_convenio_cena_domingo",
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
