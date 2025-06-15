from django.db import migrations

def copy_catalogos(apps, schema_editor):
    catalogos = [
        'TipoAccesoComedor',
        'TipoFrecuenciaInsumos',
        'TipoInsumos',
        'TipoTecnologia',
        'TipoDistanciaTransporte',
        'TipoModalidadPrestacion',
        'FrecuenciaLimpieza',
        'TipoDesague',
        'TipoGestionQuejas',
        'TipoEspacio',
        'CantidadColaboradores',
        'FrecuenciaRecepcionRecursos',
        'TipoRecurso',
        'MotivoExcepcion',
        'TipoFrecuenciaBolsones',
        'TipoModuloBolsones',
    ]

    for modelo in catalogos:
        OldModel = apps.get_model('comedores', modelo)
        NewModel = apps.get_model('relevamientos', modelo)

        for old in OldModel.objects.all():
            NewModel.objects.update_or_create(
                id=old.id,
                defaults={"nombre": old.nombre}
            )

def reverse(apps, schema_editor):
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('relevamientos', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(copy_catalogos, reverse),
    ]
