from django.db import migrations


AUDITLOG_TABLE = "auditlog_logentry"
INDEX_DEFINITIONS = (
    (
        "atl_le_ct_objpk_ts_id_idx",
        "CREATE INDEX atl_le_ct_objpk_ts_id_idx "
        "ON auditlog_logentry (content_type_id, object_pk, timestamp, id)",
    ),
    (
        "atl_le_actor_ts_id_idx",
        "CREATE INDEX atl_le_actor_ts_id_idx "
        "ON auditlog_logentry (actor_id, timestamp, id)",
    ),
    (
        "atl_le_action_ts_id_idx",
        "CREATE INDEX atl_le_action_ts_id_idx "
        "ON auditlog_logentry (action, timestamp, id)",
    ),
)
FULLTEXT_INDEX_NAME = "atl_le_changes_text_ftx"


def _is_mysql(schema_editor):
    return getattr(schema_editor.connection, "vendor", "") == "mysql"


def _table_exists(schema_editor, table_name):
    with schema_editor.connection.cursor() as cursor:
        existing_tables = schema_editor.connection.introspection.table_names(cursor)
    return table_name in existing_tables


def _index_exists(schema_editor, index_name):
    db_name = schema_editor.connection.settings_dict.get("NAME")
    if not db_name:
        return False
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT 1
            FROM information_schema.statistics
            WHERE table_schema = %s
              AND table_name = %s
              AND index_name = %s
            LIMIT 1
            """,
            [db_name, AUDITLOG_TABLE, index_name],
        )
        return cursor.fetchone() is not None


def _column_exists(schema_editor, column_name):
    db_name = schema_editor.connection.settings_dict.get("NAME")
    if not db_name:
        return False
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT 1
            FROM information_schema.columns
            WHERE table_schema = %s
              AND table_name = %s
              AND column_name = %s
            LIMIT 1
            """,
            [db_name, AUDITLOG_TABLE, column_name],
        )
        return cursor.fetchone() is not None


def add_mysql_auditlog_indexes(apps, schema_editor):
    if not _is_mysql(schema_editor):
        return
    if not _table_exists(schema_editor, AUDITLOG_TABLE):
        return

    for index_name, sql in INDEX_DEFINITIONS:
        if _index_exists(schema_editor, index_name):
            continue
        schema_editor.execute(sql)

    if _column_exists(schema_editor, "changes_text") and not _index_exists(
        schema_editor, FULLTEXT_INDEX_NAME
    ):
        schema_editor.execute(
            "CREATE FULLTEXT INDEX "
            f"{FULLTEXT_INDEX_NAME} ON {AUDITLOG_TABLE} (changes_text)"
        )


def remove_mysql_auditlog_indexes(apps, schema_editor):
    if not _is_mysql(schema_editor):
        return
    if not _table_exists(schema_editor, AUDITLOG_TABLE):
        return

    for index_name, _sql in INDEX_DEFINITIONS:
        if _index_exists(schema_editor, index_name):
            schema_editor.execute(f"DROP INDEX {index_name} ON {AUDITLOG_TABLE}")

    if _index_exists(schema_editor, FULLTEXT_INDEX_NAME):
        schema_editor.execute(f"DROP INDEX {FULLTEXT_INDEX_NAME} ON {AUDITLOG_TABLE}")


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("audittrail", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(
            add_mysql_auditlog_indexes,
            remove_mysql_auditlog_indexes,
        ),
    ]
