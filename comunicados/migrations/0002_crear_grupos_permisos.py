# Migración histórica mantenida por compatibilidad.
# La creación de grupos de comunicados se realiza únicamente en bootstrap
# mediante users.management.commands.create_groups.

from django.db import migrations


def crear_grupos(apps, schema_editor):
    """No-op: la creación de grupos se resuelve en bootstrap."""
    return


def eliminar_grupos(apps, schema_editor):
    """No-op: no se eliminan grupos en migraciones."""
    return


class Migration(migrations.Migration):

    dependencies = [
        ("comunicados", "0001_initial"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.RunPython(crear_grupos, eliminar_grupos),
    ]
