"""DB-backed regression tests for admisiones service helpers."""

import pytest

from admisiones.models.admisiones import (
    Admision,
    ArchivoAdmision,
    Documentacion,
    TipoConvenio,
)
from admisiones.services import admisiones_service as module


pytestmark = pytest.mark.django_db


def _crear_admision_con_documentos_obligatorios(cantidad=3):
    tipo_convenio = TipoConvenio.objects.create(
        nombre=f"Convenio test {TipoConvenio.objects.count() + 1}"
    )
    admision = Admision.objects.create(tipo_convenio=tipo_convenio)

    for indice in range(cantidad):
        documentacion = Documentacion.objects.create(
            nombre=f"Documento {indice}",
            obligatorio=True,
            orden=indice,
        )
        documentacion.convenios.add(tipo_convenio)
        ArchivoAdmision.objects.create(
            admision=admision,
            documentacion=documentacion,
            estado="Aceptado",
            archivo=f"admisiones/test-{indice}.pdf",
        )

    return admision


def test_todos_obligatorios_aceptados_evita_n_plus_one(db, django_assert_num_queries):
    admision = _crear_admision_con_documentos_obligatorios()

    with django_assert_num_queries(2):
        assert module.AdmisionService._todos_obligatorios_aceptados(admision) is True


def test_todos_obligatorios_tienen_archivos_evita_n_plus_one(
    db, django_assert_num_queries
):
    admision = _crear_admision_con_documentos_obligatorios()

    with django_assert_num_queries(2):
        assert (
            module.AdmisionService._todos_obligatorios_tienen_archivos(admision) is True
        )
