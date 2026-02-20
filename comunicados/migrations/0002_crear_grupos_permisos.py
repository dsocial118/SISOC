# Migración de datos para crear grupos de permisos de comunicados

from django.db import migrations


def crear_grupos(apps, schema_editor):
    """Crea los grupos de permisos para el módulo de comunicados."""
    Group = apps.get_model("auth", "Group")

    grupos = [
        "Comunicado Crear",
        "Comunicado Editar",
        "Comunicado Publicar",
        "Comunicado Archivar",
    ]

    for nombre_grupo in grupos:
        Group.objects.get_or_create(name=nombre_grupo)


def eliminar_grupos(apps, schema_editor):
    """Elimina los grupos de permisos (rollback)."""
    Group = apps.get_model("auth", "Group")

    grupos = [
        "Comunicado Crear",
        "Comunicado Editar",
        "Comunicado Publicar",
        "Comunicado Archivar",
    ]

    Group.objects.filter(name__in=grupos).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("comunicados", "0001_initial"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.RunPython(crear_grupos, eliminar_grupos),
    ]
