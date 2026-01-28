# Deprecar campos de archivos antiguos

from django.db import migrations, models


def actualizar_archivos_ok_con_nuevos_documentos(apps, schema_editor):
    """Actualiza el campo archivos_ok basado en los nuevos documentos."""
    ExpedienteCiudadano = apps.get_model('celiaquia', 'ExpedienteCiudadano')
    TipoDocumento = apps.get_model('celiaquia', 'TipoDocumento')
    
    tipos_requeridos = TipoDocumento.objects.filter(requerido=True, activo=True)
    
    for legajo in ExpedienteCiudadano.objects.all():
        documentos_cargados = legajo.documentos.filter(
            tipo_documento__requerido=True,
            tipo_documento__activo=True
        ).count()
        
        legajo.archivos_ok = documentos_cargados >= tipos_requeridos.count()
        legajo.save(update_fields=['archivos_ok'])


class Migration(migrations.Migration):

    dependencies = [
        ('celiaquia', '0010_tipodocumento_documentolegajo'),
    ]

    operations = [
        # Actualizar archivos_ok con el nuevo sistema
        migrations.RunPython(
            actualizar_archivos_ok_con_nuevos_documentos,
            migrations.RunPython.noop
        ),
        
        # Agregar help_text a campos deprecados
        migrations.AlterField(
            model_name='expedienteciudadano',
            name='archivo1',
            field=models.FileField(
                blank=True, 
                null=True, 
                upload_to='legajos/archivos/',
                help_text='DEPRECADO: Usar DocumentoLegajo'
            ),
        ),
        migrations.AlterField(
            model_name='expedienteciudadano',
            name='archivo2',
            field=models.FileField(
                blank=True, 
                null=True, 
                upload_to='legajos/archivos/',
                help_text='DEPRECADO: Usar DocumentoLegajo'
            ),
        ),
        migrations.AlterField(
            model_name='expedienteciudadano',
            name='archivo3',
            field=models.FileField(
                blank=True, 
                null=True, 
                upload_to='legajos/archivos/',
                help_text='DEPRECADO: Usar DocumentoLegajo'
            ),
        ),
        migrations.AlterField(
            model_name='expedienteciudadano',
            name='subsanacion_motivo',
            field=models.TextField(
                blank=True, 
                null=True,
                help_text='DEPRECADO: Usar HistorialComentarios'
            ),
        ),
        migrations.AlterField(
            model_name='expedienteciudadano',
            name='subsanacion_renaper_comentario',
            field=models.TextField(
                blank=True, 
                null=True,
                help_text='DEPRECADO: Usar HistorialComentarios'
            ),
        ),
        migrations.AlterField(
            model_name='expedienteciudadano',
            name='observacion_cruce',
            field=models.CharField(
                max_length=255, 
                blank=True, 
                null=True,
                help_text='DEPRECADO: Usar HistorialComentarios'
            ),
        ),
    ]