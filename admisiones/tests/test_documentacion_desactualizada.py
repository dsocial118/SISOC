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
    # pk=3 mapea a CATEGORIA_PERSONERIA en CATEGORIA_ORGANIZACIONAL_POR_TIPO_CONVENIO;
    # sin este mapeo _tokens_org_actuales devuelve {} y el centinela nunca dispararia.
    tipo_convenio = TipoConvenio.objects.create(pk=3, nombre="Personería Jurídica")
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


# ---------------------------------------------------------------------------
# Regresion Bug A — legajo con docs al crear la admision (#1799)
# ---------------------------------------------------------------------------


@pytest.fixture
def setup_legajo_con_dos_docs():
    """Admision creada cuando el legajo ya tenia dos documentos con archivos.
    Representa el path 'legajo con docs al crear' del Bug A."""
    tipo = TipoEntidad.objects.create(nombre="Personería Jurídica")
    organizacion = Organizacion.objects.create(
        nombre="Org Multi Doc", tipo_entidad=tipo
    )
    comedor = Comedor.objects.create(nombre="Comedor Multi", organizacion=organizacion)
    # pk=3 mapea a CATEGORIA_PERSONERIA en CATEGORIA_ORGANIZACIONAL_POR_TIPO_CONVENIO.
    tipo_convenio = TipoConvenio.objects.create(pk=3, nombre="Personería Jurídica")
    doc_org_1 = DocumentacionOrganizacion.objects.create(
        nombre="DNI del Presidente",
        categoria=DocumentacionOrganizacion.CATEGORIA_PERSONERIA,
        obligatorio=True,
        orden=0,
    )
    archivo_org_1 = ArchivoOrganizacion.objects.create(
        organizacion=organizacion,
        documentacion=doc_org_1,
        archivo="organizaciones/documentacion/dni.pdf",
        estado=ArchivoOrganizacion.ESTADO_PENDIENTE,
    )
    doc_org_2 = DocumentacionOrganizacion.objects.create(
        nombre="Estatuto Social Vigente",
        categoria=DocumentacionOrganizacion.CATEGORIA_PERSONERIA,
        obligatorio=True,
        orden=1,
    )
    ArchivoOrganizacion.objects.create(
        organizacion=organizacion,
        documentacion=doc_org_2,
        archivo="organizaciones/documentacion/estatuto.pdf",
        estado=ArchivoOrganizacion.ESTADO_PENDIENTE,
    )
    admision = Admision.objects.create(
        comedor=comedor,
        tipo_convenio=tipo_convenio,
        tipo_entidad_origen=tipo,
        estado_admision="documentacion_en_proceso",
    )
    # Inicializar snapshot como lo hace create_admision (legajo ya con docs).
    AdmisionService.refrescar_snapshot_documentacion_organizacional(admision)
    return {
        "admision": admision,
        "archivo_org_1": archivo_org_1,
    }


def test_primer_doc_en_legajo_multidoc_dispara_advertencia(setup_legajo_con_dos_docs):
    """Bug A regresion: modificar el PRIMER doc del legajo (mas antiguo por id)
    cuando la admision fue creada con el legajo ya con docs debe disparar la
    advertencia. El snapshot no debe tener centinela en este path."""
    admision = setup_legajo_con_dos_docs["admision"]
    archivo_org_1 = setup_legajo_con_dos_docs["archivo_org_1"]

    snaps = list(AdmisionDocOrgSnapshot.objects.filter(admision=admision))
    assert not any(s.slot_key == "__init__" for s in snaps), (
        "No debe existir centinela __init__ cuando el legajo tenia docs al crear la admision"
    )
    assert len(snaps) == 2, "Debe haber un snapshot por cada doc del legajo"

    # Modificar el PRIMER documento del legajo (mas antiguo por orden e id).
    archivo_org_1.estado = ArchivoOrganizacion.ESTADO_ACEPTADO
    archivo_org_1.save(update_fields=["estado"])

    desactualizada, labels = AdmisionService.admision_documentacion_desactualizada(
        admision
    )
    assert desactualizada is True, (
        "La modificacion del primer doc debe disparar la advertencia"
    )
    assert "DNI del Presidente" in labels
    assert "Estatuto Social Vigente" not in labels


def test_segundo_doc_en_legajo_multidoc_dispara_advertencia(setup_legajo_con_dos_docs):
    """Simetria del Bug A: modificar el segundo doc tambien debe disparar la
    advertencia (para confirmar que no hay sesgo por orden)."""
    admision = setup_legajo_con_dos_docs["admision"]

    archivos = list(
        ArchivoOrganizacion.objects.filter(
            organizacion=admision.comedor.organizacion
        ).order_by("id")
    )
    archivo_org_2 = archivos[1]  # segundo por id

    archivo_org_2.estado = ArchivoOrganizacion.ESTADO_ACEPTADO
    archivo_org_2.save(update_fields=["estado"])

    desactualizada, labels = AdmisionService.admision_documentacion_desactualizada(
        admision
    )
    assert desactualizada is True
    assert "Estatuto Social Vigente" in labels
    assert "DNI del Presidente" not in labels


def test_sin_cambios_no_dispara_advertencia_con_legajo_con_docs(
    setup_legajo_con_dos_docs,
):
    """Con snapshot inicializado y sin cambios en el legajo, no debe aparecer
    advertencia (verificacion de no falso positivo)."""
    admision = setup_legajo_con_dos_docs["admision"]

    desactualizada, labels = AdmisionService.admision_documentacion_desactualizada(
        admision
    )
    assert desactualizada is False
    assert labels == []
