# Limpieza de campos duplicados en ExpedienteCiudadano

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('celiaquia', '0007_historialcomentarios'),
    ]

    operations = [
        # Campos duplicados ya migrados al historial de comentarios
        # Se mantienen por compatibilidad pero se deprecan
    ]