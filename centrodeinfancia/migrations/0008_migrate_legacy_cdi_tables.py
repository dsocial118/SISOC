import datetime

from django.db import migrations


def _column_names(cursor, connection, table_name):
    description = connection.introspection.get_table_description(cursor, table_name)
    return {column.name for column in description}


def _copy_rows_with_mapping(
    cursor, connection, source_table, target_table, column_mapping
):
    source_columns = _column_names(cursor, connection, source_table)
    target_columns = _column_names(cursor, connection, target_table)

    mapped_columns = [
        (source_column, target_column)
        for source_column, target_column in column_mapping.items()
        if source_column in source_columns and target_column in target_columns
    ]
    if not mapped_columns:
        return

    target_column_set = {target for _, target in mapped_columns}
    if "id" not in target_column_set:
        return

    quote_name = connection.ops.quote_name
    target_ids_query = f"SELECT id FROM {quote_name(target_table)}"
    cursor.execute(target_ids_query)
    existing_target_ids = {row[0] for row in cursor.fetchall()}

    source_select_columns = ", ".join(
        quote_name(source_column) for source_column, _ in mapped_columns
    )
    source_rows_query = (
        f"SELECT {source_select_columns} FROM {quote_name(source_table)}"
    )
    cursor.execute(source_rows_query)
    source_rows = cursor.fetchall()

    insert_target_columns = [target_column for _, target_column in mapped_columns]
    insert_target_columns_sql = ", ".join(
        quote_name(target_column) for target_column in insert_target_columns
    )
    insert_placeholders = ", ".join(["%s"] * len(insert_target_columns))
    insert_query = (
        f"INSERT INTO {quote_name(target_table)} "
        f"({insert_target_columns_sql}) VALUES ({insert_placeholders})"
    )

    for row_values in source_rows:
        row_data = {
            target_column: value
            for (_, target_column), value in zip(mapped_columns, row_values)
        }
        row_id = row_data.get("id")
        if row_id in existing_target_ids:
            continue

        fecha_inicio = row_data.get("fecha_inicio")
        if isinstance(fecha_inicio, int):
            try:
                row_data["fecha_inicio"] = datetime.date(fecha_inicio, 1, 1)
            except ValueError:
                row_data["fecha_inicio"] = None

        insert_values = [row_data[column] for column in insert_target_columns]
        cursor.execute(insert_query, insert_values)
        existing_target_ids.add(row_id)


def migrate_legacy_cdi_tables(apps, schema_editor):
    connection = schema_editor.connection
    quote_name = connection.ops.quote_name

    with connection.cursor() as cursor:
        existing_tables = set(connection.introspection.table_names(cursor))

        table_mappings = [
            (
                "cdi_centrodeinfancia",
                "centrodeinfancia_centrodeinfancia",
                {
                    "id": "id",
                    "nombre": "nombre",
                    "organizacion_id": "organizacion_id",
                    "provincia_id": "provincia_id",
                    "municipio_id": "municipio_id",
                    "localidad_id": "localidad_id",
                    "calle": "calle",
                    "telefono": "telefono",
                    "nombre_referente": "nombre_referente",
                    "apellido_referente": "apellido_referente",
                    "email_referente": "email_referente",
                    "telefono_referente": "telefono_referente",
                    "fecha_inicio": "fecha_inicio",
                    "fecha_creacion": "fecha_creacion",
                    "deleted_at": "deleted_at",
                    "deleted_by_id": "deleted_by_id",
                },
            ),
            (
                "cdi_nominacentroinfancia",
                "centrodeinfancia_nominacentroinfancia",
                {
                    "id": "id",
                    "centro_id": "centro_id",
                    "ciudadano_id": "ciudadano_id",
                    "fecha": "fecha",
                    "estado": "estado",
                    "observaciones": "observaciones",
                    "deleted_at": "deleted_at",
                    "deleted_by_id": "deleted_by_id",
                },
            ),
            (
                "cdi_intervencioncentroinfancia",
                "centrodeinfancia_intervencioncentroinfancia",
                {
                    "id": "id",
                    "centro_id": "centro_id",
                    "tipo_intervencion_id": "tipo_intervencion_id",
                    "subintervencion_id": "subintervencion_id",
                    "destinatario_id": "destinatario_id",
                    "forma_contacto_id": "forma_contacto_id",
                    "fecha": "fecha",
                    "observaciones": "observaciones",
                    "tiene_documentacion": "tiene_documentacion",
                    "documentacion": "documentacion",
                    "deleted_at": "deleted_at",
                    "deleted_by_id": "deleted_by_id",
                },
            ),
            (
                "cdi_observacioncentroinfancia",
                "centrodeinfancia_observacioncentroinfancia",
                {
                    "id": "id",
                    "centro_id": "centro_id",
                    "observador": "observador",
                    "fecha_visita": "fecha_visita",
                    "observacion": "observacion",
                    "deleted_at": "deleted_at",
                    "deleted_by_id": "deleted_by_id",
                },
            ),
            (
                "cdi_centrodesarrolloinfantil",
                "centrodeinfancia_centrodeinfancia",
                {
                    "id": "id",
                    "nombre": "nombre",
                    "organizacion_id": "organizacion_id",
                    "provincia_id": "provincia_id",
                    "municipio_id": "municipio_id",
                    "localidad_id": "localidad_id",
                    "direccion": "calle",
                    "telefono": "telefono",
                    "email": "email_referente",
                    "comienzo": "fecha_inicio",
                },
            ),
        ]

        for source_table, target_table, column_mapping in table_mappings:
            if (
                source_table not in existing_tables
                or target_table not in existing_tables
            ):
                continue

            # Skip if source table is empty to avoid unnecessary locks/writes.
            cursor.execute(f"SELECT 1 FROM {quote_name(source_table)} LIMIT 1")
            if cursor.fetchone() is None:
                continue

            _copy_rows_with_mapping(
                cursor,
                connection,
                source_table,
                target_table,
                column_mapping,
            )


class Migration(migrations.Migration):
    dependencies = [
        ("centrodeinfancia", "0007_centrodeinfancia_apellido_referente"),
    ]

    operations = [
        migrations.RunPython(
            migrate_legacy_cdi_tables,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
