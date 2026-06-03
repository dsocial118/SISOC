"""Tests para el flujo de resincronizacion Admision <-> Organizacion (Seccion 1
del issue #1605)."""

import pytest

from admisiones.models.admisiones import (
    Admision,
    AdmisionDocOrgSnapshot,
    ArchivoAdmision,
    Documentacion,
    EstadoAdmision,
    TipoConvenio,
)
from admisiones.services.admisiones_service import AdmisionService
from admisiones.services.tipo_convenio_resolver import (
    admision_desincronizada,
    categoria_para_organizacion,
)
from comedores.models import Comedor
from organizaciones.models import (
    DocumentacionOrganizacion,
    Organizacion,
    TipoEntidad,
)


pytestmark = pytest.mark.django_db


@pytest.fixture
def estado_inicial():
    return EstadoAdmision.objects.create(nombre="Pendiente")


@pytest.fixture
def tipo_entidades():
    juridica = TipoEntidad.objects.create(nombre="Personería Jurídica")
    eclesiastica = TipoEntidad.objects.create(nombre="Personería Jurídica Eclesiástica")
    hecho = TipoEntidad.objects.create(nombre="Asociación de Hecho")
    return {"juridica": juridica, "eclesiastica": eclesiastica, "hecho": hecho}


@pytest.fixture
def tipos_convenio():
    base = TipoConvenio.objects.create(pk=1, nombre="Organización Base")
    eclesiastica = TipoConvenio.objects.create(
        pk=2, nombre="Personería Jurídica Eclesiástica"
    )
    juridica = TipoConvenio.objects.create(pk=3, nombre="Personería Jurídica")
    return {"base": base, "eclesiastica": eclesiastica, "juridica": juridica}


def _crear_admision(tipo_entidad, tipo_convenio, estado_inicial):
    organizacion = Organizacion.objects.create(
        nombre="Org Test", tipo_entidad=tipo_entidad
    )
    comedor = Comedor.objects.create(nombre="Comedor Test", organizacion=organizacion)
    return Admision.objects.create(
        comedor=comedor,
        tipo_convenio=tipo_convenio,
        tipo_entidad_origen=tipo_entidad,
        estado=estado_inicial,
        estado_admision="documentacion_en_proceso",
    )


def test_admision_desincronizada_devuelve_false_cuando_snapshot_coincide(
    estado_inicial, tipo_entidades, tipos_convenio
):
    admision = _crear_admision(
        tipo_entidades["juridica"], tipos_convenio["juridica"], estado_inicial
    )

    assert AdmisionService.admision_desincronizada(admision) is False
    assert admision_desincronizada(admision) is False


def test_admision_desincronizada_devuelve_true_cuando_org_cambia_tipo(
    estado_inicial, tipo_entidades, tipos_convenio
):
    admision = _crear_admision(
        tipo_entidades["juridica"], tipos_convenio["juridica"], estado_inicial
    )
    admision.comedor.organizacion.tipo_entidad = tipo_entidades["eclesiastica"]
    admision.comedor.organizacion.save(update_fields=["tipo_entidad"])
    admision.refresh_from_db()

    assert AdmisionService.admision_desincronizada(admision) is True
    assert admision_desincronizada(admision) is True


def test_admision_desincronizada_false_si_falta_tipo_actual(
    estado_inicial, tipos_convenio
):
    organizacion = Organizacion.objects.create(nombre="Org sin tipo")
    comedor = Comedor.objects.create(
        nombre="Comedor sin tipo", organizacion=organizacion
    )
    admision = Admision.objects.create(
        comedor=comedor,
        tipo_convenio=tipos_convenio["juridica"],
        estado=estado_inicial,
    )

    assert AdmisionService.admision_desincronizada(admision) is False


def test_admision_legacy_sin_snapshot_se_inicializa_lazy(
    estado_inicial, tipo_entidades, tipos_convenio
):
    """Una admision creada antes del snapshot (o por un flujo que no lo seteaba)
    debe adoptar como base el ``tipo_entidad`` actual de la organizacion la
    primera vez que se evalua la desincronizacion."""

    organizacion = Organizacion.objects.create(
        nombre="Org legacy", tipo_entidad=tipo_entidades["juridica"]
    )
    comedor = Comedor.objects.create(nombre="Comedor legacy", organizacion=organizacion)
    admision = Admision.objects.create(
        comedor=comedor,
        tipo_convenio=tipos_convenio["juridica"],
        estado=estado_inicial,
    )
    assert admision.tipo_entidad_origen_id is None

    desincronizada = AdmisionService.admision_desincronizada(admision)

    admision.refresh_from_db()
    assert desincronizada is False
    assert admision.tipo_entidad_origen_id == tipo_entidades["juridica"].id

    # Despues del lazy init, un cambio en la organizacion si debe disparar la
    # advertencia.
    organizacion.tipo_entidad = tipo_entidades["eclesiastica"]
    organizacion.save(update_fields=["tipo_entidad"])
    admision.refresh_from_db()
    assert AdmisionService.admision_desincronizada(admision) is True


def test_resync_admision_borra_archivos_y_actualiza_snapshot(
    estado_inicial, tipo_entidades, tipos_convenio
):
    admision = _crear_admision(
        tipo_entidades["juridica"], tipos_convenio["juridica"], estado_inicial
    )
    documentacion = Documentacion.objects.create(nombre="DNI", obligatorio=True)
    documentacion.convenios.add(tipos_convenio["juridica"])
    ArchivoAdmision.objects.create(
        admision=admision,
        documentacion=documentacion,
        estado="Aceptado",
        archivo="admisiones/test.pdf",
    )
    admision.comedor.organizacion.tipo_entidad = tipo_entidades["eclesiastica"]
    admision.comedor.organizacion.save(update_fields=["tipo_entidad"])

    ok, mensaje = AdmisionService.resync_admision_desde_organizacion(admision)

    assert ok is True
    assert "Legajo" in mensaje
    admision.refresh_from_db()
    assert admision.tipo_entidad_origen_id == tipo_entidades["eclesiastica"].id
    assert (
        admision.tipo_convenio_id == tipos_convenio["eclesiastica"].id
    ), "El tipo_convenio debe quedar mapeado al nuevo tipo_entidad"
    assert (
        ArchivoAdmision.objects.filter(admision=admision).count() == 0
    ), "Todos los archivos previos deben quedar eliminados"


def test_resync_admision_falla_si_no_hay_organizacion(estado_inicial):
    admision = Admision.objects.create(
        comedor=None, estado=estado_inicial, estado_admision="documentacion_en_proceso"
    )

    ok, mensaje = AdmisionService.resync_admision_desde_organizacion(admision)

    assert ok is False
    assert "organizacion" in mensaje.lower()


def test_aceptar_desincronizacion_solo_actualiza_snapshot(
    estado_inicial, tipo_entidades, tipos_convenio
):
    admision = _crear_admision(
        tipo_entidades["juridica"], tipos_convenio["juridica"], estado_inicial
    )
    documentacion = Documentacion.objects.create(nombre="DNI", obligatorio=True)
    documentacion.convenios.add(tipos_convenio["juridica"])
    archivo = ArchivoAdmision.objects.create(
        admision=admision,
        documentacion=documentacion,
        estado="Aceptado",
        archivo="admisiones/test.pdf",
    )
    admision.comedor.organizacion.tipo_entidad = tipo_entidades["eclesiastica"]
    admision.comedor.organizacion.save(update_fields=["tipo_entidad"])

    ok, _ = AdmisionService.aceptar_desincronizacion_admision(admision)

    assert ok is True
    admision.refresh_from_db()
    assert admision.tipo_entidad_origen_id == tipo_entidades["eclesiastica"].id
    assert (
        admision.tipo_convenio_id == tipos_convenio["juridica"].id
    ), "El tipo_convenio NO debe modificarse al aceptar la desincronizacion"
    assert ArchivoAdmision.objects.filter(
        pk=archivo.pk
    ).exists(), "Los archivos previos deben preservarse al continuar con la admision"
    assert AdmisionService.admision_desincronizada(admision) is False


def test_aceptar_desincronizacion_no_materializa_archivos_nuevos(
    estado_inicial, tipo_entidades, tipos_convenio
):
    """Bug B regresion: 'Continuar' (aceptar_desincronizacion) NO debe crear
    ArchivoAdmision nuevos para slots que la admision no tenia materializados.
    El slot del legajo sigue siendo 'live' (via organizacion) en la vista."""
    from organizaciones.models import ArchivoOrganizacion, DocumentacionOrganizacion

    admision = _crear_admision(
        tipo_entidades["juridica"], tipos_convenio["juridica"], estado_inicial
    )
    # Doc en el legajo que la admision nunca materializó.
    doc_org = DocumentacionOrganizacion.objects.create(
        nombre="DNI del Presidente",
        categoria=DocumentacionOrganizacion.CATEGORIA_PERSONERIA,
        obligatorio=True,
    )
    ArchivoOrganizacion.objects.create(
        organizacion=admision.comedor.organizacion,
        documentacion=doc_org,
        archivo="organizaciones/documentacion/dni.pdf",
        estado=ArchivoOrganizacion.ESTADO_PENDIENTE,
    )
    AdmisionService.refrescar_snapshot_documentacion_organizacional(admision)
    count_antes = ArchivoAdmision.objects.filter(admision=admision).count()

    ok, _ = AdmisionService.aceptar_desincronizacion_admision(admision)

    assert ok is True
    count_despues = ArchivoAdmision.objects.filter(admision=admision).count()
    assert count_despues == count_antes, (
        "Continuar operando NO debe materializar ArchivoAdmision nuevos desde el legajo"
    )
    # El snapshot si debe actualizarse para silenciar la advertencia.
    snaps = list(AdmisionDocOrgSnapshot.objects.filter(admision=admision))
    assert any(s.slot_key != "__init__" for s in snaps), (
        "El snapshot debe registrar el doc del legajo tras aceptar"
    )


def test_categoria_para_organizacion_mapea_por_nombre(tipo_entidades):
    org_juridica = Organizacion.objects.create(
        nombre="J", tipo_entidad=tipo_entidades["juridica"]
    )
    org_eclesiastica = Organizacion.objects.create(
        nombre="E", tipo_entidad=tipo_entidades["eclesiastica"]
    )
    org_hecho = Organizacion.objects.create(
        nombre="H", tipo_entidad=tipo_entidades["hecho"]
    )

    assert (
        categoria_para_organizacion(org_juridica)
        == DocumentacionOrganizacion.CATEGORIA_PERSONERIA
    )
    assert (
        categoria_para_organizacion(org_eclesiastica)
        == DocumentacionOrganizacion.CATEGORIA_ECLESIASTICA
    )
    assert (
        categoria_para_organizacion(org_hecho)
        == DocumentacionOrganizacion.CATEGORIA_BASE
    )
