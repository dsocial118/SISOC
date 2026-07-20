from django.db import migrations
from django.utils import timezone


ARCA_NOMBRE = "Constancia de inscripcion ante ARCA"
ARCA_CATEGORIAS = ("personeria_juridica", "personeria_eclesiastica")

AVALES = (
    (
        "Acta de Designación de Avales - Designación de cargo Avales  (persona fisica o juridica)",
        (
            "Acta Designacion Aval 1 - Designacion de cargo Aval 1 (persona fisica o juridica)",
            "Acta Designacion Aval 2 - Designacion de cargo Aval 2 (persona fisica o juridica)",
        ),
        True,
    ),
    (
        "DNI de la Autoridad Máxima Avales / DNI Avales (según corresponda)",
        (
            "DNI de la Autoridad Maxima del Aval 1 / DNI del Aval 1 (segun corresponda)",
            "DNI de la Autoridad Maxima del Aval 2 / DNI del Aval 2 (segun corresponda)",
        ),
        True,
    ),
    (
        "Nota Avales",
        ("Nota de aval emitida por el Aval 1", "Nota de aval emitida por el Aval 2"),
        True,
    ),
    (
        "Acta constitutiva Avales",
        ("Acta constitutiva del Aval 1", "Acta constitutiva del Aval 2"),
        False,
    ),
    ("Estatuto de Avales", ("Estatuto del Aval 1", "Estatuto del Aval 2"), False),
    (
        "Resolucion de Personeria Juridica Avales",
        (
            "Resolucion de Personeria Juridica del Aval 1",
            "Resolucion de Personeria Juridica del Aval 2",
        ),
        False,
    ),
)


def actualizar_documentacion(apps, schema_editor):
    Documentacion = apps.get_model("organizaciones", "DocumentacionOrganizacion")
    Archivo = apps.get_model("organizaciones", "ArchivoOrganizacion")

    arca_ids = list(
        Documentacion.objects.filter(
            nombre=ARCA_NOMBRE, categoria__in=ARCA_CATEGORIAS
        ).values_list("id", flat=True)
    )
    Archivo.objects.filter(
        documentacion_id__in=arca_ids, deleted_at__isnull=True
    ).update(deleted_at=timezone.now())
    Documentacion.objects.filter(id__in=arca_ids).delete()

    for nuevo_nombre, nombres_anteriores, obligatorio in AVALES:
        anteriores = list(
            Documentacion.objects.filter(
                categoria="organizacion_base", nombre__in=nombres_anteriores
            ).order_by("orden", "id")
        )
        orden = anteriores[0].orden if anteriores else 0
        destino, _ = Documentacion.objects.get_or_create(
            categoria="organizacion_base",
            nombre=nuevo_nombre,
            defaults={"obligatorio": obligatorio, "orden": orden},
        )
        destino.obligatorio = obligatorio
        destino.orden = orden
        destino.save(update_fields=["obligatorio", "orden"])
        origen_ids = [
            documento.id for documento in anteriores if documento.id != destino.id
        ]
        Archivo.objects.filter(documentacion_id__in=origen_ids).update(
            documentacion_id=destino.id
        )
        Documentacion.objects.filter(id__in=origen_ids).delete()


class Migration(migrations.Migration):

    dependencies = [("organizaciones", "0015_quitar_acta_solicitud_subsidio")]

    operations = [
        migrations.RunPython(actualizar_documentacion, migrations.RunPython.noop),
    ]
