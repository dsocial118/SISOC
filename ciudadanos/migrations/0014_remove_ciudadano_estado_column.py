from django.db import migrations


def drop_estado_column(apps, schema_editor):
    """
    Remove the legacy `estado` column left in the DB when the field was
    dropped from the model. Before dropping it, copy its value into the
    `activo` column so existing data keeps the same status.
    """

    connection = schema_editor.connection
    quote = schema_editor.quote_name
    table = "ciudadanos_ciudadano"
    estado_col = "estado"
    activo_col = "activo"

    with connection.cursor() as cursor:
        existing_tables = set(connection.introspection.table_names(cursor))

    if table not in existing_tables:
        return

    def column_exists(column: str) -> bool:
        with connection.cursor() as cursor:
            columns = connection.introspection.get_table_description(cursor, table)
        return any(col.name == column for col in columns)

    if not column_exists(estado_col):
        return

    if not column_exists(activo_col):
        schema_editor.execute(
            f"ALTER TABLE {quote(table)} ADD COLUMN {quote(activo_col)} BOOL NOT NULL DEFAULT 1"
        )

    schema_editor.execute(
        f"""
        UPDATE {quote(table)}
        SET {quote(activo_col)} = {quote(estado_col)}
        WHERE {quote(estado_col)} IS NOT NULL
        """
    )
    schema_editor.execute(
        f"ALTER TABLE {quote(table)} DROP COLUMN {quote(estado_col)}"
    )


class Migration(migrations.Migration):

    dependencies = [
        ("ciudadanos", "0013_fix_grupofamiliar_text_fields"),
    ]

    operations = [
        migrations.RunPython(drop_estado_column, migrations.RunPython.noop),
    ]
