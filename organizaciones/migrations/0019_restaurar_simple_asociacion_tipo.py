from django.db import migrations


NOMBRE_SIMPLE_ASOCIACION = "Simple Asociación (art. 187 CCCN)"


def restaurar_simple_asociacion_como_tipo(apps, schema_editor):
    TipoEntidad = apps.get_model("organizaciones", "TipoEntidad")

    simple_asociacion = (
        TipoEntidad.objects.filter(nombre__iexact=NOMBRE_SIMPLE_ASOCIACION)
        .order_by("pk")
        .first()
    )
    if simple_asociacion is None:
        TipoEntidad.objects.create(nombre=NOMBRE_SIMPLE_ASOCIACION)
    elif simple_asociacion.nombre != NOMBRE_SIMPLE_ASOCIACION:
        simple_asociacion.nombre = NOMBRE_SIMPLE_ASOCIACION
        simple_asociacion.save(update_fields=["nombre"])


class Migration(migrations.Migration):

    dependencies = [
        ("organizaciones", "0018_corregir_simple_asociacion_subtipo"),
    ]

    operations = [
        migrations.RunPython(
            restaurar_simple_asociacion_como_tipo,
            migrations.RunPython.noop,
        ),
    ]
