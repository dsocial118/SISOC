"""Issue #1799 (feedback punto 1): "Actualizar Información desde Legajo Organización"
DIRIGIDO. Debe refrescar solo los documentos org cuyo slot cambió y PRESERVAR los
documentos nativos de la admisión (cargados admisión-side) y los org no modificados,
sin resetear tipo_convenio ni estado. Antes borraba TODOS los ArchivoAdmision.

Incluye regresion Bug 2: docs de origen org con estado Aceptado en la admision
no deben borrarse al actualizar (fix #1799)."""

import pytest

from admisiones.models.admisiones import (
    Admision,
    ArchivoAdmision,
    Documentacion,
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
    organizacion = Organizacion.objects.create(nombre="Org Dir", tipo_entidad=tipo)
    comedor = Comedor.objects.create(nombre="Comedor Dir", organizacion=organizacion)
    EstadoAdmision.objects.create(pk=1, nombre="Pendiente")
    tipo_convenio = TipoConvenio.objects.create(pk=3, nombre="Personería Jurídica")
    admision = Admision.objects.create(
        comedor=comedor,
        tipo_convenio=tipo_convenio,
        tipo_entidad_origen=tipo,
        estado_admision="documentacion_en_proceso",
    )

    # Documento de catálogo de la Organización + su par aliasado en la Admisión.
    doc_org = DocumentacionOrganizacion.objects.create(
        nombre="DNI del Presidente",
        categoria=DocumentacionOrganizacion.CATEGORIA_PERSONERIA,
        obligatorio=True,
    )
    archivo_org = ArchivoOrganizacion.objects.create(
        organizacion=organizacion,
        documentacion=doc_org,
        archivo="organizaciones/dni.pdf",
        estado=ArchivoOrganizacion.ESTADO_PENDIENTE,
    )
    doc_adm = Documentacion.objects.create(nombre="DNI Presidente", obligatorio=True)
    doc_adm.convenios.add(tipo_convenio)

    # Materializar (org -> admisión) y dejar el snapshot en sync.
    AdmisionService.congelar_documentacion_organizacional(admision)
    AdmisionService.refrescar_snapshot_documentacion_organizacional(admision)

    # Documento NATIVO de la admisión (cargado admisión-side): debe preservarse.
    doc_nativo = Documentacion.objects.create(nombre="Memo PNUD", obligatorio=True)
    doc_nativo.convenios.add(tipo_convenio)
    archivo_nativo = ArchivoAdmision.objects.create(
        admision=admision,
        documentacion=doc_nativo,
        archivo="admisiones/memo.pdf",
        estado="aceptado",
        numero_gde="GDE-NATIVO-1",
    )

    return {
        "admision": admision,
        "archivo_org": archivo_org,
        "doc_adm": doc_adm,
        "archivo_nativo": archivo_nativo,
    }


def _archivo_org_materializado(admision, doc_adm):
    return ArchivoAdmision.objects.filter(
        admision=admision, documentacion=doc_adm
    ).first()


def test_actualizar_refresca_doc_cambiado_y_preserva_nativo(setup):
    admision = setup["admision"]
    materializado_previo = _archivo_org_materializado(admision, setup["doc_adm"])
    assert materializado_previo is not None
    assert materializado_previo.archivo_organizacion_origen_id is not None
    convenio_previo = admision.tipo_convenio_id
    estado_admision_previo = admision.estado_admision

    # Cambio SOLO de documentación: el doc org pasa Pendiente -> Aceptado.
    setup["archivo_org"].estado = ArchivoOrganizacion.ESTADO_ACEPTADO
    setup["archivo_org"].save(update_fields=["estado"])

    ok, _ = AdmisionService.actualizar_documentacion_desde_organizacion(admision)
    assert ok is True

    # El doc org materializado se refrescó al nuevo estado.
    materializado = _archivo_org_materializado(admision, setup["doc_adm"])
    assert materializado is not None
    assert materializado.estado == ArchivoOrganizacion.ESTADO_ACEPTADO

    # El doc NATIVO se preservó intacto (mismo registro, mismo GDE).
    nativo = ArchivoAdmision.objects.get(pk=setup["archivo_nativo"].pk)
    assert nativo.estado == "aceptado"
    assert nativo.numero_gde == "GDE-NATIVO-1"
    assert nativo.archivo_organizacion_origen_id is None

    # No se reseteó convenio ni estado de la admisión.
    admision.refresh_from_db()
    assert admision.tipo_convenio_id == convenio_previo
    assert admision.estado_admision == estado_admision_previo


def test_actualizar_sin_cambios_no_toca_nada(setup):
    admision = setup["admision"]
    materializado_previo = _archivo_org_materializado(admision, setup["doc_adm"])
    nativo_previo_pk = setup["archivo_nativo"].pk

    ok, mensaje = AdmisionService.actualizar_documentacion_desde_organizacion(admision)

    assert ok is True
    # El doc org materializado sigue siendo el mismo registro (no se recreó).
    materializado = _archivo_org_materializado(admision, setup["doc_adm"])
    assert materializado.pk == materializado_previo.pk
    assert ArchivoAdmision.objects.filter(pk=nativo_previo_pk).exists()


def test_actualizar_quita_doc_removido_del_legajo_y_preserva_nativo(setup):
    admision = setup["admision"]

    # El documento se quita del legajo (pierde su archivo => deja de estar vigente).
    setup["archivo_org"].archivo = ""
    setup["archivo_org"].save(update_fields=["archivo"])

    ok, _ = AdmisionService.actualizar_documentacion_desde_organizacion(admision)
    assert ok is True

    # El ArchivoAdmision de origen organizacional se quitó.
    assert _archivo_org_materializado(admision, setup["doc_adm"]) is None
    # El doc nativo se preservó.
    assert ArchivoAdmision.objects.filter(pk=setup["archivo_nativo"].pk).exists()


# ---------------------------------------------------------------------------
# Regresion Bug 2 — docs Aceptados en admision no deben borrarse al actualizar
# ---------------------------------------------------------------------------


def test_actualizar_preserva_doc_aceptado_de_origen_org(setup):
    """Un ArchivoAdmision de origen organizacional con estado Aceptado (validado
    por un tecnico desde la admision) NO debe eliminarse al actualizar, aunque el
    slot haya cambiado en el legajo."""
    admision = setup["admision"]
    doc_adm = setup["doc_adm"]

    # Obtener el ArchivoAdmision materializado y marcarlo como Aceptado
    # (simula validacion manual desde la admision).
    materializado = _archivo_org_materializado(admision, doc_adm)
    assert materializado is not None
    materializado.estado = "Aceptado"
    materializado.save(update_fields=["estado"])
    pk_aceptado = materializado.pk

    # Cambiar el archivo en el legajo (dispara un cambio de slot).
    setup["archivo_org"].estado = ArchivoOrganizacion.ESTADO_ACEPTADO
    setup["archivo_org"].save(update_fields=["estado"])

    ok, _ = AdmisionService.actualizar_documentacion_desde_organizacion(admision)
    assert ok is True

    # El doc Aceptado de origen org debe haberse conservado.
    assert ArchivoAdmision.objects.filter(
        pk=pk_aceptado
    ).exists(), (
        "El ArchivoAdmision con estado Aceptado no debe eliminarse al actualizar"
    )
    conservado = ArchivoAdmision.objects.get(pk=pk_aceptado)
    assert conservado.estado == "Aceptado"


def test_actualizar_refresca_doc_aceptado_cuando_cambia_el_archivo(setup):
    """Bug sincronizacion de adjuntos: si el archivo del legajo cambia realmente
    (la organizacion sube un adjunto nuevo), el documento de origen organizacional
    debe refrescarse en la admision AUNQUE su copia este "Aceptado" — de lo
    contrario la admision sigue mostrando el adjunto viejo. Solo los cambios de
    metadatos (estado/observaciones) preservan la validacion."""
    admision = setup["admision"]
    doc_adm = setup["doc_adm"]
    organizacion = admision.comedor.organizacion

    # La copia materializada en la admision quedo validada (Aceptado) sobre el
    # archivo viejo del legajo.
    materializado = _archivo_org_materializado(admision, doc_adm)
    assert materializado is not None
    nombre_viejo = materializado.archivo.name
    materializado.estado = "Aceptado"
    materializado.save(update_fields=["estado"])

    # La organizacion sube un ADJUNTO NUEVO: como el doc estaba Aceptado, el flujo
    # real crea una nueva version (nueva fila ArchivoOrganizacion vigente).
    ArchivoOrganizacion.objects.create(
        organizacion=organizacion,
        documentacion=setup["archivo_org"].documentacion,
        archivo="organizaciones/dni_v2.pdf",
        estado=ArchivoOrganizacion.ESTADO_ADJUNTO,
    )

    ok, _ = AdmisionService.actualizar_documentacion_desde_organizacion(admision)
    assert ok is True

    # La admision debe mostrar AHORA el archivo nuevo, no el viejo.
    refrescado = _archivo_org_materializado(admision, doc_adm)
    assert refrescado is not None
    assert refrescado.archivo.name == "organizaciones/dni_v2.pdf"
    assert refrescado.archivo.name != nombre_viejo
