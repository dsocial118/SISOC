from django.db import migrations


def ensure_datetime_columns(apps, schema_editor):
    """
    The state switched ciudadano.creado/modificado to DateTimeField in
    0009, but the DB columns stayed as DATE because the migration only
    changed state. On MySQL that returns `datetime.date` instances and
    Django fails when trying to make them timezone-aware. Convert both
    columns to DATETIME(6) and backfill nulls before the type change.
    """

    connection = schema_editor.connection
    if connection.vendor != "mysql":
        # Only MySQL/MariaDB needs the manual column type fix.
        return

    quote = schema_editor.quote_name
    table = quote("ciudadanos_ciudadano")
    created_col = quote("creado")
    modified_col = quote("modificado")

    with connection.cursor() as cursor:
        cursor.execute(
            f"""
            UPDATE {table}
            SET {created_col} = COALESCE({created_col}, CURRENT_TIMESTAMP(6)),
                {modified_col} = COALESCE({modified_col}, CURRENT_TIMESTAMP(6));
            """
        )
        cursor.execute(
            f"""
            ALTER TABLE {table}
            MODIFY {created_col} DATETIME(6) NOT NULL,
            MODIFY {modified_col} DATETIME(6) NOT NULL;
            """
        )


class Migration(migrations.Migration):

    dependencies = [
        ("ciudadanos", "0011_alter_ciudadanoprograma_fecha_creado"),
    ]

    operations = [
        migrations.RunPython(
            ensure_datetime_columns, reverse_code=migrations.RunPython.noop
        ),
    ]
