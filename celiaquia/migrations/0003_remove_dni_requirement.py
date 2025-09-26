# Generated migration to remove DNI document requirement

from django.db import migrations


def update_archivos_ok_field(apps, schema_editor):
    """
    Actualizar el campo archivos_ok para que solo considere archivo2 y archivo3
    """
    ExpedienteCiudadano = apps.get_model('celiaquia', 'ExpedienteCiudadano')
    
    # Actualizar todos los registros existentes
    for legajo in ExpedienteCiudadano.objects.all():
        # Nuevo cálculo: solo archivo2 y archivo3
        legajo.archivos_ok = bool(legajo.archivo2 and legajo.archivo3)
        legajo.save(update_fields=['archivos_ok'])


def reverse_archivos_ok_field(apps, schema_editor):
    """
    Revertir el campo archivos_ok para que considere archivo1, archivo2 y archivo3
    """
    ExpedienteCiudadano = apps.get_model('celiaquia', 'ExpedienteCiudadano')
    
    # Revertir al cálculo original
    for legajo in ExpedienteCiudadano.objects.all():
        # Cálculo original: archivo1, archivo2 y archivo3
        legajo.archivos_ok = bool(legajo.archivo1 and legajo.archivo2 and legajo.archivo3)
        legajo.save(update_fields=['archivos_ok'])


class Migration(migrations.Migration):

    dependencies = [
        ('celiaquia', '0002_expediente_numero_expediente_and_more'),
    ]

    operations = [
        migrations.RunPython(
            update_archivos_ok_field,
            reverse_archivos_ok_field,
        ),
    ]