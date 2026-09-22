from django.db import migrations


def quitar_firma_de_respuestas(apps, schema_editor):
    declaracion_model = apps.get_model("pas", "PasDeclaracionJurada")
    for declaracion in declaracion_model.objects.only("id", "respuestas").iterator():
        respuestas = declaracion.respuestas or {}
        if "firma_nombre_completo" not in respuestas:
            continue
        respuestas = dict(respuestas)
        respuestas.pop("firma_nombre_completo", None)
        declaracion_model.objects.filter(pk=declaracion.pk).update(
            respuestas=respuestas
        )


class Migration(migrations.Migration):
    dependencies = [
        ("pas", "0007_paspersona_genero_calle_altura"),
    ]

    operations = [
        migrations.RunPython(quitar_firma_de_respuestas, migrations.RunPython.noop),
    ]
