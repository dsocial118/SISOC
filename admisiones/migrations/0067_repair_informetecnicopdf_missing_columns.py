# Generated manually in FAST mode.

from django.db import migrations


def repair_informetecnicopdf_missing_columns(apps, schema_editor):
    InformeTecnicoPDF = apps.get_model("admisiones", "InformeTecnicoPDF")
    table_name = InformeTecnicoPDF._meta.db_table
    with schema_editor.connection.cursor() as cursor:
        existing_columns = {
            column.name
            for column in schema_editor.connection.introspection.get_table_description(
                cursor,
                table_name,
            )
        }
    for field_name in ("archivo_docx_editado",):
        if field_name in existing_columns:
            continue
        schema_editor.add_field(
            InformeTecnicoPDF, InformeTecnicoPDF._meta.get_field(field_name)
        )
        existing_columns.add(field_name)


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("admisiones", "0066_repair_informetecnico_missing_columns"),
    ]

    operations = [
        migrations.RunPython(
            repair_informetecnicopdf_missing_columns,
            migrations.RunPython.noop,
        ),
    ]
