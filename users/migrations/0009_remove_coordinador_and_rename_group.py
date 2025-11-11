# Generated migration - Combined operations

from django.db import migrations


def rename_coordinador_group(apps, schema_editor):
    """Renombra el grupo 'Coordinador Gestion' a 'Coordinador Equipo Tecnico'"""
    Group = apps.get_model('auth', 'Group')
    try:
        group = Group.objects.get(name='Coordinador Gestion')
        group.name = 'Coordinador Equipo Tecnico'
        group.save()
    except Group.DoesNotExist:
        # Si no existe, no hay nada que renombrar
        pass


def reverse_rename_coordinador_group(apps, schema_editor):
    """Revertir: renombra de vuelta a 'Coordinador Gestion'"""
    Group = apps.get_model('auth', 'Group')
    try:
        group = Group.objects.get(name='Coordinador Equipo Tecnico')
        group.name = 'Coordinador Gestion'
        group.save()
    except Group.DoesNotExist:
        pass


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0008_add_es_coordinador_and_duplas'),
    ]

    operations = [
        # Renombrar grupo
        migrations.RunPython(rename_coordinador_group, reverse_rename_coordinador_group),
    ]
