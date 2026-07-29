import unicodedata

from django.db import migrations


def _normalizar_nombre(nombre):
    sin_acentos = unicodedata.normalize("NFD", nombre or "")
    sin_acentos = "".join(
        caracter for caracter in sin_acentos if not unicodedata.combining(caracter)
    )
    return " ".join(sin_acentos.lower().split())


def limpiar_codigos_alimentar_comunidad(apps, schema_editor):
    """Elimina códigos que no aplican al programa Alimentar Comunidad."""
    comedor_model = apps.get_model("comedores", "Comedor")
    programa_model = apps.get_model("comedores", "Programas")
    programas_alimentar_ids = [
        programa.pk
        for programa in programa_model.objects.only("id", "nombre")
        if _normalizar_nombre(programa.nombre) == "alimentar comunidad"
    ]

    if programas_alimentar_ids:
        comedor_model.objects.filter(programa_id__in=programas_alimentar_ids).update(
            codigo_de_proyecto=None
        )


class Migration(migrations.Migration):

    dependencies = [
        ("comedores", "0051_comedor_categoria_espacio_comunitario"),
    ]

    operations = [
        migrations.RunPython(
            limpiar_codigos_alimentar_comunidad,
            migrations.RunPython.noop,
        ),
    ]
