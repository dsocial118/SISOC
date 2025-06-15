from django.db import migrations

def copy_catalogos_extra(apps, schema_editor):
    catalogos = [
        "TipoAgua",
        "TipoCombustible",
        "TipoDesague",
        "TipoEspacio",
        "TipoGestionQuejas",
        "FrecuenciaLimpieza",
        "TipoTecnologia",
        "TipoDistanciaTransporte",
        "TipoModalidadPrestacion",
    ]

    for nombre_modelo in catalogos:
        OldModel = apps.get_model("comedores", nombre_modelo)
        NewModel = apps.get_model("relevamientos", nombre_modelo)

        for old in OldModel.objects.all():
            # Se asume que todos estos modelos tienen al menos el campo `nombre`
            NewModel.objects.update_or_create(
                id=old.id,
                defaults={
                    field.name: getattr(old, field.name)
                    for field in OldModel._meta.fields
                    if field.name != "id"
                }
            )

def reverse(apps, schema_editor):
    # No se implementa reversión
    pass

class Migration(migrations.Migration):

    dependencies = [
        ("relevamientos", "0002_copy_catalogos"),  # ajustá si el nombre real difiere
    ]

    operations = [
        migrations.RunPython(copy_catalogos_extra, reverse),
    ]
