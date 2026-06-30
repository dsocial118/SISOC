"""Asegura un DEFAULT a nivel de base de datos para `es_interno`.

En MySQL, `AddField(BooleanField(default=False))` crea la columna NOT NULL sin
DEFAULT (Django aplica el default en Python). Si un INSERT omite la columna
(p. ej. por un desfasaje entre el código y la migración aplicada), MySQL aborta
con error 1364. Fijar el DEFAULT a 0 en la base hace el INSERT resiliente y
coincide con el default del modelo. No-op en motores que no son MySQL (sqlite de
los tests ya inserta la columna vía ORM).
"""

from django.db import migrations


TABLE = "celiaquia_historialcomentarios"
COLUMN = "es_interno"


def set_db_default(apps, schema_editor):
    if schema_editor.connection.vendor != "mysql":
        return
    schema_editor.execute(f"ALTER TABLE {TABLE} ALTER COLUMN {COLUMN} SET DEFAULT 0;")


def drop_db_default(apps, schema_editor):
    if schema_editor.connection.vendor != "mysql":
        return
    schema_editor.execute(f"ALTER TABLE {TABLE} ALTER COLUMN {COLUMN} DROP DEFAULT;")


class Migration(migrations.Migration):

    # MySQL no puede hacer rollback de DDL: la migración no debe ejecutarse
    # dentro de una transacción (de lo contrario Django prohíbe el ALTER).
    atomic = False

    dependencies = [
        ("celiaquia", "0003_historialcomentarios_es_interno"),
    ]

    operations = [
        migrations.RunPython(set_db_default, drop_db_default),
    ]
