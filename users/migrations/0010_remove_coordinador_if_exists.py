# Generated migration - Conditional removal of coordinador field

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def remove_coordinador_field_if_exists(apps, schema_editor):
    """
    Elimina el campo coordinador de Profile solo si existe en la base de datos.
    Esto maneja el caso donde la migración 0006 puede o no haberse aplicado.
    """
    if schema_editor.connection.vendor == 'mysql':
        # Para MySQL, intentamos eliminar la columna solo si existe
        with schema_editor.connection.cursor() as cursor:
            # Verificar si la columna existe
            cursor.execute("""
                SELECT COUNT(*)
                FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = 'users_profile'
                AND COLUMN_NAME = 'coordinador_id'
            """)
            exists = cursor.fetchone()[0] > 0

            if exists:
                # Buscar el nombre de la foreign key constraint
                cursor.execute("""
                    SELECT CONSTRAINT_NAME
                    FROM information_schema.KEY_COLUMN_USAGE
                    WHERE TABLE_SCHEMA = DATABASE()
                    AND TABLE_NAME = 'users_profile'
                    AND COLUMN_NAME = 'coordinador_id'
                    AND REFERENCED_TABLE_NAME IS NOT NULL
                """)
                fk_result = cursor.fetchone()

                # Si existe una FK, eliminarla primero
                if fk_result:
                    fk_name = fk_result[0]
                    cursor.execute(
                        f"ALTER TABLE `users_profile` DROP FOREIGN KEY `{fk_name}`"
                    )

                # Ahora eliminar la columna
                cursor.execute(
                    "ALTER TABLE `users_profile` DROP COLUMN `coordinador_id`"
                )


def noop(apps, schema_editor):
    """No-op para el reverso."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('users', '0009_remove_coordinador_and_rename_group'),
    ]

    operations = [
        # Separar las operaciones de estado y base de datos
        migrations.SeparateDatabaseAndState(
            # Operaciones de estado: eliminar el campo del modelo
            state_operations=[
                migrations.RemoveField(
                    model_name='profile',
                    name='coordinador',
                ),
            ],
            # Operaciones de base de datos: eliminar condicionalmente si existe
            database_operations=[
                migrations.RunPython(
                    remove_coordinador_field_if_exists,
                    noop,
                ),
            ],
        ),
    ]
