# Generated migration

from django.db import migrations, models


def migrate_programa_from_ciudadanos(apps, schema_editor):
    """Copiar datos de ciudadanos.Programa a core.Programa"""
    try:
        ProgramaOld = apps.get_model('ciudadanos', 'Programa')
        ProgramaNew = apps.get_model('core', 'Programa')
        
        for old in ProgramaOld.objects.all():
            ProgramaNew.objects.create(
                id=old.id,
                nombre=old.nombre,
                estado=old.estado,
                observaciones=old.observaciones,
            )
    except Exception:
        pass  # Si no existe el modelo antiguo, continuar


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_alter_provincia_nombre'),
    ]

    operations = [
        migrations.CreateModel(
            name='Programa',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=255, unique=True)),
                ('estado', models.BooleanField(default=True)),
                ('observaciones', models.CharField(blank=True, max_length=500, null=True)),
            ],
            options={
                'verbose_name': 'Programa',
                'verbose_name_plural': 'Programas',
                'ordering': ['nombre'],
            },
        ),
        migrations.RunPython(migrate_programa_from_ciudadanos, migrations.RunPython.noop),
    ]
