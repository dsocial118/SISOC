# Generated by Django 4.0.2 on 2024-09-23 16:23

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('legajos', '0004_direccion_estadosintervencion_estadosllamados_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='dimensionfamilia',
            name='estado_civil',
        ),
    ]
