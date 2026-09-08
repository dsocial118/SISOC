from django.db import migrations


TITULO_IMPORTACION_NOMINA = "Importación de nómina"


def archivar_comunicados_importacion_nomina(apps, schema_editor):
    Comunicado = apps.get_model("comunicados", "Comunicado")
    Comunicado.objects.filter(
        tipo="interno",
        estado="publicado",
        titulo__istartswith=TITULO_IMPORTACION_NOMINA,
    ).update(
        estado="archivado",
        destacado=False,
    )


class Migration(migrations.Migration):
    dependencies = [
        ("comunicados", "0009_comunicado_organizaciones"),
    ]

    operations = [
        migrations.RunPython(
            archivar_comunicados_importacion_nomina,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
