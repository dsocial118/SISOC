import importlib

import pytest
from django.apps import apps
from django.core.files.uploadedfile import SimpleUploadedFile

from admisiones.models.admisiones import Admision, ArchivoAdmision, Documentacion
from comedores.models import Comedor
from organizaciones.models import (
    ArchivoOrganizacion,
    DocumentacionOrganizacion,
    Organizacion,
)


@pytest.mark.django_db
def test_migracion_arca_materializa_archivo_en_admision():
    organizacion = Organizacion.objects.create(nombre="Organizacion ARCA")
    comedor = Comedor.objects.create(nombre="Espacio ARCA", organizacion=organizacion)
    admision = Admision.objects.create(comedor=comedor)
    documento = DocumentacionOrganizacion.objects.create(
        nombre="Constancia de inscripcion ante ARCA",
        categoria="personeria_juridica",
    )
    archivo = ArchivoOrganizacion.objects.create(
        organizacion=organizacion,
        documentacion=documento,
        archivo=SimpleUploadedFile("arca.pdf", b"%PDF"),
    )
    Documentacion.objects.filter(nombre="Constancia de ARCA").delete()

    migracion = importlib.import_module(
        "organizaciones.migrations.0016_issue_2083_documentacion_organizacion"
    )
    migracion.actualizar_documentacion(apps, None)

    materializado = ArchivoAdmision.objects.get(
        admision=admision, archivo_organizacion_origen=archivo
    )
    assert materializado.documentacion.nombre == "Constancia de ARCA"
    assert materializado.archivo.name == archivo.archivo.name
    archivo.refresh_from_db()
    assert archivo.deleted_at is not None
