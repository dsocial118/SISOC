# Basada en la migración generada; se le agregó el paso que conserva la
# localidad ya cargada antes de borrar la columna.

from django.db import migrations, models


def copiar_localidad_a_localidades(apps, schema_editor):
    """Pasa la localidad única de cada operativo al nuevo M2M."""
    Relevamiento = apps.get_model("datacalle", "Relevamiento")
    for relevamiento in Relevamiento.objects.exclude(localidad__isnull=True).iterator():
        relevamiento.localidades.add(relevamiento.localidad_id)


def volver_a_localidad_unica(apps, schema_editor):
    """Al revertir, conserva la primera localidad de cada operativo."""
    Relevamiento = apps.get_model("datacalle", "Relevamiento")
    for relevamiento in Relevamiento.objects.iterator():
        primera = relevamiento.localidades.first()
        if primera is not None:
            relevamiento.localidad_id = primera.id
            relevamiento.save(update_fields=["localidad"])


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0008_programa_organismo_programa_descripcion"),
        ("datacalle", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="relevamiento",
            name="localidades",
            field=models.ManyToManyField(
                blank=True,
                help_text="Un operativo puede abarcar varias zonas del mismo municipio.",
                related_name="relevamientos_datacalle",
                to="core.localidad",
                verbose_name="Localidades / comunas",
            ),
        ),
        migrations.RunPython(
            copiar_localidad_a_localidades,
            volver_a_localidad_unica,
        ),
        migrations.RemoveField(
            model_name="relevamiento",
            name="localidad",
        ),
    ]
