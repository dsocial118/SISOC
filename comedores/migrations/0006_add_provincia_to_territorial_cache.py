# Generated manually for territorial cache provincia migration

import logging

from django.db import migrations, models
import django.db.models.deletion


logger = logging.getLogger("django")


def limpiar_cache_territorial(apps, schema_editor):
    """
    Limpia el cache territorial existente ya que será regenerado por provincia.
    """
    TerritorialCache = apps.get_model('comedores', 'TerritorialCache')
    TerritorialSyncLog = apps.get_model('comedores', 'TerritorialSyncLog')

    # Limpiar cache existente - será regenerado con el nuevo sistema
    deleted_count = TerritorialCache.objects.all().count()
    TerritorialCache.objects.all().delete()

    logger.info(
        "Eliminados %s registros de cache territorial existentes", deleted_count
    )
    logger.info(
        "El cache será regenerado automáticamente por provincia en el primer uso"
    )


def reverse_limpiar_cache(apps, schema_editor):
    """
    No hay forma de revertir la limpieza de datos, pero no es crítico
    ya que el cache se regenera automáticamente.
    """
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),  # Asumiendo que core tiene el modelo Provincia
        ('comedores', '0005_territorialcache_territorialsynclog'),
    ]

    operations = [
        # 1. Limpiar datos existentes antes de cambiar el schema
        migrations.RunPython(limpiar_cache_territorial, reverse_limpiar_cache),
        
        # 2. Agregar el campo provincia
        migrations.AddField(
            model_name='territorialcache',
            name='provincia',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.provincia'),
        ),
        
        # 3. Eliminar la constraint unique en gestionar_uid solo
        migrations.AlterField(
            model_name='territorialcache',
            name='gestionar_uid',
            field=models.CharField(max_length=100),  # Quitar unique=True
        ),
        
        # 4. Agregar nuevo unique_together y índices
        migrations.AlterUniqueTogether(
            name='territorialcache',
            unique_together={('gestionar_uid', 'provincia')},
        ),
        
        # 5. Agregar índice para performance
        migrations.AddIndex(
            model_name='territorialcache',
            index=models.Index(fields=['provincia', 'activo'], name='comedores_territorial_provincia_activo_idx'),
        ),
        
        # 6. Actualizar ordenamiento
        migrations.AlterModelOptions(
            name='territorialcache',
            options={'ordering': ['provincia__nombre', 'nombre'], 'verbose_name': 'Cache Territorial', 'verbose_name_plural': 'Cache Territoriales'},
        ),
    ]
