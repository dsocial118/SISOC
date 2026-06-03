"""Tests del Req 1 del issue #1799: advertencia ante cambios en la documentacion
del legajo de la Organizacion (snapshot por admision + diff).

Incluye tests de regresion para bugs reportados en la implementacion:
- Bug 1: la primera modificacion en el legajo no disparaba la advertencia
  (fix: centinela __init__ en AdmisionDocOrgSnapshot).
- Bug 2: docs con estado Aceptado en la admision no se conservaban al actualizar."""

import pytest

from admisiones.models.admisiones import (
    Admision,
    AdmisionDocOrgSnapshot,
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
    organizacion = Organizacion.objects.create(nombre="Org Adv", tipo_entidad=tipo)
    comedor = Comedor.objects.create(nombre="Comedor Adv", organizacion=organizacion)
    EstadoAdmision.objects.create(pk=1, nombre="Pendiente")
    EstadoAdmision.objects.create(pk=2, nombre="Doc en proceso")
    tipo_convenio = TipoConvenio.objects.create(pk=3, nombre="Personería Jurídica")
    admision = Admision.objects.create(
        comedor=comedor,
        tipo_convenio=tipo_convenio,
        tipo_entidad_origen=tipo,
        estado_admision="documentacion_en_proceso",
    )
    doc_org = DocumentacionOrganizacion.objects.create(
        nombre="DNI del Presidente",
        categoria=DocumentacionOrganizacion.CATEGORIA_PERSONERIA,
        obligatorio=True,
    )
    archivo_org = ArchivoOrganizacion.objects.create(
        organizacion=organizacion,
        documentacion=doc_org,
        archivo="organizaciones/documentacion/dni.pdf",
        estado=ArchivoOrganizacion.ESTADO_PENDIENTE,
    )
    return {
        "organizacion": organizacion,
        "admision": admision,
        "doc_org": doc_org,
        "archivo_org": archivo_org,
    }


def test_lazy_init_sin_snapshot_arranca_en_sync(setup):
    assert not AdmisionDocOrgSnapshot.objects.filter(
        admision=setup["admision"]
    ).exists()
    desactualizada, labels = AdmisionService.admision_documentacion_desactualizada(
        setup["admision"]
    )
    assert desactualizada is False
    assert labels == []
    # Se inicializo el snapshot.
    assert AdmisionDocOrgSnapshot.objects.filter(admision=setup["admision"]).exists()


def test_cambio_de_estado_dispara_advertencia(setup):
    AdmisionService.refrescar_snapshot_documentacion_organizacional(setup["admision"])

    # Pendiente -> Aceptado (req 1.7)
    setup["archivo_org"].estado = ArchivoOrganizacion.ESTADO_ACEPTADO
    setup["archivo_org"].save(update_fields=["estado"])

    desactualizada, labels = AdmisionService.admision_documentacion_desactualizada(
        setup["admision"]
    )
    assert desactualizada is True
    assert "DNI del Presidente" in labels


def test_aceptar_divergencia_silencia_la_advertencia(setup):
    AdmisionService.refrescar_snapshot_documentacion_organizacional(setup["admision"])
    setup["archivo_org"].estado = ArchivoOrganizacion.ESTADO_ACEPTADO
    setup["archivo_org"].save(update_fields=["estado"])

    AdmisionService.aceptar_desincronizacion_admision(setup["admision"])

    desactualizada, labels = AdmisionService.admision_documentacion_desactualizada(
        setup["admision"]
    )
    assert desactualizada is False
    assert labels == []


def test_documento_adicional_nuevo_dispara_advertencia(setup):
    AdmisionService.refrescar_snapshot_documentacion_organizacional(setup["admision"])

    ArchivoOrganizacion.objects.create(
        organizacion=setup["organizacion"],
        documentacion=None,
        nombre_personalizado="Nota adicional",
        archivo="organizaciones/documentacion/nota.pdf",
        estado=ArchivoOrganizacion.ESTADO_ADJUNTO,
    )

    desactualizada, labels = AdmisionService.admision_documentacion_desactualizada(
        setup["admision"]
    )
    assert desactualizada is True
    assert "Nota adicional" in labels


def test_cambio_de_vencimiento_dispara_advertencia(setup):
    import datetime

    AdmisionService.refrescar_snapshot_documentacion_organizacional(setup["admision"])

    setup["archivo_org"].fecha_vencimiento = datetime.date(2027, 1, 1)
    setup["archivo_org"].save(update_fields=["fecha_vencimiento"])

    desactualizada, labels = AdmisionService.admision_documentacion_desactualizada(
        setup["admision"]
    )
    assert desactualizada is True
    assert "DNI del Presidente" in labels


# ---------------------------------------------------------------------------
# Regresion Bug 1 — primera modificacion no disparaba advertencia (#1799)
# ---------------------------------------------------------------------------


@pytest.fixture
def setup_legajo_vacio():
    """Admision creada cuando el legajo de la org todavia no tenia archivos."""
    tipo = TipoEntidad.objects.create(nombre="Personería Jurídica")
    organizacion = Organizacion.objects.create(nombre="Org Sin Docs", tipo_entidad=tipo)
    comedor = Comedor.objects.create(
        nombre="Comedor Sin Docs", organizacion=organizacion
    )
    EstadoAdmision.objects.create(pk=11, nombre="Pendiente")
    tipo_convenio = TipoConvenio.objects.create(pk=13, nombre="Personería Jurídica")
    doc_org = DocumentacionOrganizacion.objects.create(
        nombre="DNI del Presidente",
        categoria=DocumentacionOrganizacion.CATEGORIA_PERSONERIA,
        obligatorio=True,
    )
    admision = Admision.objects.create(
        comedor=comedor,
        tipo_convenio=tipo_convenio,
        tipo_entidad_origen=tipo,
        estado_admision="documentacion_en_proceso",
    )
    # Inicializar snapshot con legajo vacio (condicion reproductora del bug).
    AdmisionService.refrescar_snapshot_documentacion_organizacional(admision)
    return {
        "organizacion": organizacion,
        "admision": admision,
        "doc_org": doc_org,
    }


def test_primera_carga_en_legajo_dispara_advertencia(setup_legajo_vacio):
    """Bug 1: la primera vez que se sube un archivo al legajo debe disparar la
    advertencia en la admision, no silenciarse por el lazy-init del snapshot."""
    admision = setup_legajo_vacio["admision"]
    doc_org = setup_legajo_vacio["doc_org"]
    organizacion = setup_legajo_vacio["organizacion"]

    # Verificar que el snapshot fue inicializado (solo centinela __init__).
    snaps = list(AdmisionDocOrgSnapshot.objects.filter(admision=admision))
    assert any(
        s.slot_key == "__init__" for s in snaps
    ), "Debe existir el centinela __init__ tras inicializar con legajo vacio"

    # Primera carga de archivo en el legajo.
    ArchivoOrganizacion.objects.create(
        organizacion=organizacion,
        documentacion=doc_org,
        archivo="organizaciones/documentacion/dni.pdf",
        estado=ArchivoOrganizacion.ESTADO_ADJUNTO,
    )

    desactualizada, labels = AdmisionService.admision_documentacion_desactualizada(
        admision
    )
    assert (
        desactualizada is True
    ), "La primera modificacion del legajo debe disparar la advertencia"
    assert "DNI del Presidente" in labels


def test_segunda_carga_tambien_dispara_advertencia(setup_legajo_vacio):
    """Tras la primera carga (que disparo la advertencia y fue aceptada), la
    segunda modificacion del legajo tambien debe disparar la advertencia."""
    admision = setup_legajo_vacio["admision"]
    doc_org = setup_legajo_vacio["doc_org"]
    organizacion = setup_legajo_vacio["organizacion"]

    # Primera carga + aceptar divergencia (silencia y avanza la linea base).
    archivo = ArchivoOrganizacion.objects.create(
        organizacion=organizacion,
        documentacion=doc_org,
        archivo="organizaciones/documentacion/dni.pdf",
        estado=ArchivoOrganizacion.ESTADO_ADJUNTO,
    )
    AdmisionService.aceptar_desincronizacion_admision(admision)

    # Segunda modificacion: cambio de estado.
    archivo.estado = ArchivoOrganizacion.ESTADO_ACEPTADO
    archivo.save(update_fields=["estado"])

    desactualizada, labels = AdmisionService.admision_documentacion_desactualizada(
        admision
    )
    assert desactualizada is True
    assert "DNI del Presidente" in labels
