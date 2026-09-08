from django.db import migrations


TITULO_IMPORTACION_NOMINA = "Importación de nómina"


def archivar_comunicado_importacion_nomina_con_prefijo(apps, schema_editor):
    Comunicado = apps.get_model("comunicados", "Comunicado")
    Comunicado.objects.filter(
        tipo="interno",
        estado="publicado",
        titulo__icontains=TITULO_IMPORTACION_NOMINA,
    ).update(
        estado="archivado",
        destacado=False,
    )


class Migration(migrations.Migration):
    dependencies = [
        ("comunicados", "0011_rearchive_importacion_nomina"),
    ]

    operations = [
        migrations.RunPython(
            archivar_comunicado_importacion_nomina_con_prefijo,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
