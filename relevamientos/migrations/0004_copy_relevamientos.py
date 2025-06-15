from django.db import migrations, connection


def copy_relevamientos(apps, schema_editor):
    OldRel = apps.get_model("comedores", "Relevamiento")
    NewRel = apps.get_model("relevamientos", "Relevamiento")

    nuevos = []
    for old in OldRel.objects.all().iterator():
        nuevos.append(
            NewRel(
                id=old.id,  # mantenemos la PK
                estado=old.estado,
                comedor_id=old.comedor_id,
                fecha_visita=old.fecha_visita,
                territorial_nombre=old.territorial_nombre,
                territorial_uid=old.territorial_uid,
                funcionamiento_id=old.funcionamiento_id,
                espacio_id=old.espacio_id,
                colaboradores_id=old.colaboradores_id,
                recursos_id=old.recursos_id,
                compras_id=old.compras_id,
                prestacion_id=old.prestacion_id,
                observacion=old.observacion,
                docPDF=old.docPDF,
                responsable_es_referente=old.responsable_es_referente,
                responsable_relevamiento_id=old.responsable_relevamiento_id,
                anexo_id=old.anexo_id,
                excepcion_id=old.excepcion_id,
                imagenes=old.imagenes,
                punto_entregas_id=old.punto_entregas_id,
            )
        )

    if nuevos:
        NewRel.objects.bulk_create(nuevos, ignore_conflicts=True)


class Migration(migrations.Migration):

    dependencies = [
        ("relevamientos", "0003_copy_modelos_relacionados"),
    ]

    operations = [
        migrations.RunPython(copy_relevamientos, migrations.RunPython.noop),
    ]
