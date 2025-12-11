# Generated manually to update display text for documentacion_finalizada

from django.db import migrations


def update_estado_mostrar(apps, schema_editor):
    """Update estado_mostrar for records with documentacion_finalizada"""
    Admision = apps.get_model('admisiones', 'Admision')
    
    # Update records where estado_mostrar is the old text
    Admision.objects.filter(
        estado_mostrar='Documentación finalizada'
    ).update(
        estado_mostrar='Documentación cargada'
    )


def reverse_update_estado_mostrar(apps, schema_editor):
    """Reverse the update (for rollback)"""
    Admision = apps.get_model('admisiones', 'Admision')
    
    # Revert records back to old text
    Admision.objects.filter(
        estado_mostrar='Documentación cargada'
    ).update(
        estado_mostrar='Documentación finalizada'
    )


class Migration(migrations.Migration):

    dependencies = [
        ('admisiones', '0039_alter_admision_estado_admision_and_more'),
    ]

    operations = [
        migrations.RunPython(
            update_estado_mostrar,
            reverse_update_estado_mostrar
        ),
    ]