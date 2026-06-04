"""Tests de la Fase 0 del issue #1799: la materializacion de documentacion
organizacional debe registrar la procedencia en
``ArchivoAdmision.archivo_organizacion_origen``."""

import pytest

from admisiones.models.admisiones import (
    Admision,
    ArchivoAdmision,
    EstadoAdmision,
    TipoConvenio,
)
from admisiones.services.admisiones_service import AdmisionService
from comedores.models import Comedor
from organizaciones.models import (
    ArchivoOrganizacion,
    DocumentacionOrganizacion,
    Organizacion,
    TipoEntidad,
)


pytestmark = pytest.mark.django_db


@pytest.fixture
def setup():
    tipo = TipoEntidad.objects.create(nombre="Personería Jurídica")
    organizacion = Organizacion.objects.create(nombre="Org 1799", tipo_entidad=tipo)
    comedor = Comedor.objects.create(nombre="Comedor 1799", organizacion=organizacion)
    # El servicio setea ``admision.estado_id = 2`` al sincronizar el estado
    # documental, por lo que necesitamos que existan ambos EstadoAdmision.
    EstadoAdmision.objects.create(pk=1, nombre="Pendiente")
    EstadoAdmision.objects.create(pk=2, nombre="Documentación en proceso")
    tipo_convenio = TipoConvenio.objects.create(pk=3, nombre="Personería Jurídica")
    admision = Admision.objects.create(
        comedor=comedor,
        tipo_convenio=tipo_convenio,
        tipo_entidad_origen=tipo,
        estado_admision="documentacion_en_proceso",
    )
    documentacion_org = DocumentacionOrganizacion.objects.create(
        nombre="DNI del Presidente",
        categoria=DocumentacionOrganizacion.CATEGORIA_PERSONERIA,
        obligatorio=True,
    )
    archivo_org = ArchivoOrganizacion.objects.create(
        organizacion=organizacion,
        documentacion=documentacion_org,
        archivo="organizaciones/documentacion/dni-presidente.pdf",
        estado=ArchivoOrganizacion.ESTADO_ACEPTADO,
    )
    return {
        "admision": admision,
        "archivo_org": archivo_org,
        "organizacion": organizacion,
    }


def test_congelar_setea_archivo_organizacion_origen(setup):
    """Al materializar un ArchivoOrganizacion como ArchivoAdmision, la copia
    debe apuntar al archivo de origen via ``archivo_organizacion_origen``."""

    AdmisionService.congelar_documentacion_organizacional(setup["admision"])

    creados = ArchivoAdmision.objects.filter(admision=setup["admision"])
    assert creados.count() == 1
    archivo_adm = creados.first()
    assert archivo_adm.archivo_organizacion_origen_id == setup["archivo_org"].id
    # El nombre del archivo se copia tal cual (clave de join del backfill).
    assert archivo_adm.archivo.name == setup["archivo_org"].archivo.name
