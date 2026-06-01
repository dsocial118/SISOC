"""Issue #1799 Req 2: el "Acta de solicitud de subsidio al programa" vuelve a
gestionarse como documento nativo de la Admision. Se lo quita del catalogo de
documentacion de la Organizacion y se soft-deletean los archivos cargados para
ese documento (se preservan como historico, no se borran fisicamente)."""

from django.db import migrations
from django.utils import timezone


ACTA_NOMBRE = "Acta de solicitud de subsidio al programa"


def quitar_acta_del_legajo(apps, schema_editor):
    DocumentacionOrganizacion = apps.get_model(
        "organizaciones", "DocumentacionOrganizacion"
    )
    ArchivoOrganizacion = apps.get_model("organizaciones", "ArchivoOrganizacion")

    doc_ids = list(
        DocumentacionOrganizacion.objects.filter(nombre=ACTA_NOMBRE).values_list(
            "id", flat=True
        )
    )
    if not doc_ids:
        return

    ArchivoOrganizacion.objects.filter(
        documentacion_id__in=doc_ids, deleted_at__isnull=True
    ).update(deleted_at=timezone.now())
    DocumentacionOrganizacion.objects.filter(id__in=doc_ids).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("organizaciones", "0014_archivoorganizacion_nombre_personalizado_and_more"),
    ]

    operations = [
        migrations.RunPython(quitar_acta_del_legajo, migrations.RunPython.noop),
    ]
