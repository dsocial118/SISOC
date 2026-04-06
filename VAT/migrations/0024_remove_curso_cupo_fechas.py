from django.db import migrations


def _drop_curso_columns_if_present(apps, schema_editor):
    """Drop legacy Curso columns only when they exist (backend-agnostic)."""
    curso_model = apps.get_model("VAT", "Curso")
    table_name = curso_model._meta.db_table
    columns = ("cupo_total", "fecha_inicio", "fecha_fin")
    connection = schema_editor.connection
    introspection = connection.introspection

    with connection.cursor() as cursor:
        if table_name not in introspection.table_names(cursor):
            return

        description = introspection.get_table_description(cursor, table_name)
        existing = {
            getattr(column, "name", column[0])
            for column in description
        }

    for column_name in columns:
        if column_name in existing:
            field = curso_model._meta.get_field(column_name)
            schema_editor.remove_field(curso_model, field)


class Migration(migrations.Migration):
    dependencies = [
        ("VAT", "0023_ofertainstitucional_voucher_parametrias"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(
                    _drop_curso_columns_if_present,
                    reverse_code=migrations.RunPython.noop,
                )
            ],
            state_operations=[
                migrations.RemoveField(
                    model_name="curso",
                    name="cupo_total",
                ),
                migrations.RemoveField(
                    model_name="curso",
                    name="fecha_fin",
                ),
                migrations.RemoveField(
                    model_name="curso",
                    name="fecha_inicio",
                ),
            ],
        ),
    ]
