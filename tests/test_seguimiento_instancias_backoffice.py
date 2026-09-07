"""Alta de instancias del ciclo de seguimiento desde el backoffice (fase 3).

`PrimerSeguimientoService.create_instancia` reemplaza al guard "ya existe un
primer seguimiento" (que con N instancias bloqueaba cualquier segunda alta) y
el ancla creada desde el popup queda asignada al territorial (`territorial_user`)
para que le aparezca en la app.
"""

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from comedores.models import Comedor
from core.models import Provincia
from relevamientos.models import PrimerSeguimiento, Relevamiento
from relevamientos.primer_seguimiento_service import PrimerSeguimientoService

TERRITORIAL_JSON = '{"gestionar_uid":"%s","nombre":"Territorial Norte"}'


@pytest.fixture(autouse=True)
def _sin_gestionar(mocker):
    mocker.patch(
        "relevamientos.primer_seguimiento_service.AsyncSendPrimerSeguimientoToGestionar"
    )
    mocker.patch(
        "relevamientos.primer_seguimiento_service.AsyncSendRelevamientoToGestionar"
    )


@pytest.fixture
def comedor():
    provincia = Provincia.objects.create(nombre="Prov Instancias BO")
    return Comedor.objects.create(nombre="Comedor Instancias BO", provincia=provincia)


@pytest.fixture
def territorial():
    return get_user_model().objects.create_user(
        username="terr_bo", email="terr_bo@example.com", password="x"
    )


@pytest.mark.django_db
def test_primer_seguimiento_toma_numero_orden_1_y_origen_sisoc(comedor, territorial):
    seg = PrimerSeguimientoService.create_instancia(
        comedor.id, TERRITORIAL_JSON % territorial.id
    )

    assert seg.tipo == PrimerSeguimiento.TIPO_PRIMER
    assert seg.numero_orden == 1
    assert seg.origen == PrimerSeguimiento.ORIGEN_SISOC
    assert seg.asignado_desde_sisoc is True


@pytest.mark.django_db
def test_el_ancla_creada_desde_el_popup_queda_asignada_al_territorial(
    comedor, territorial
):
    """Sin `territorial_user` el ancla no le aparecia al territorial en la app."""
    seg = PrimerSeguimientoService.create_instancia(
        comedor.id, TERRITORIAL_JSON % territorial.id
    )

    ancla = seg.id_relevamiento
    assert ancla.territorial_uid == str(territorial.id)
    assert ancla.territorial_user_id == territorial.id


@pytest.mark.django_db
def test_segunda_instancia_toma_el_siguiente_numero_orden(comedor, territorial):
    primero = PrimerSeguimientoService.create_instancia(
        comedor.id, TERRITORIAL_JSON % territorial.id
    )

    posterior = PrimerSeguimientoService.create_instancia(
        comedor.id,
        TERRITORIAL_JSON % territorial.id,
        relevamiento_id=primero.id_relevamiento_id,
        tipo=PrimerSeguimiento.TIPO_POSTERIOR,
    )
    virtual = PrimerSeguimientoService.create_instancia(
        comedor.id,
        TERRITORIAL_JSON % territorial.id,
        relevamiento_id=primero.id_relevamiento_id,
        tipo=PrimerSeguimiento.TIPO_VIRTUAL,
    )

    assert (posterior.tipo, posterior.numero_orden) == ("posterior", 2)
    assert (virtual.tipo, virtual.numero_orden) == ("virtual", 3)
    assert posterior.id_relevamiento_id == primero.id_relevamiento_id
    assert Relevamiento.objects.filter(comedor=comedor).count() == 1


@pytest.mark.django_db
def test_no_admite_dos_primeros_seguimientos(comedor, territorial):
    primero = PrimerSeguimientoService.create_instancia(
        comedor.id, TERRITORIAL_JSON % territorial.id
    )

    with pytest.raises(ValidationError, match="Ya existe un primer seguimiento"):
        PrimerSeguimientoService.create_instancia(
            comedor.id,
            TERRITORIAL_JSON % territorial.id,
            relevamiento_id=primero.id_relevamiento_id,
            tipo=PrimerSeguimiento.TIPO_PRIMER,
        )
    assert PrimerSeguimiento.objects.count() == 1


@pytest.mark.django_db
def test_acta_de_excepcion_se_crea_como_instancia(comedor, territorial):
    seg = PrimerSeguimientoService.create_instancia(
        comedor.id,
        TERRITORIAL_JSON % territorial.id,
        tipo=PrimerSeguimiento.TIPO_ACTA_EXCEPCION,
    )

    # Sin instancia previa toma el primer numero libre.
    assert (seg.tipo, seg.numero_orden) == ("acta_excepcion", 1)


@pytest.mark.django_db
def test_tipo_desconocido_es_rechazado(comedor, territorial):
    with pytest.raises(ValidationError, match="Tipo de seguimiento no reconocido"):
        PrimerSeguimientoService.create_instancia(
            comedor.id, TERRITORIAL_JSON % territorial.id, tipo="cualquier_cosa"
        )
    assert not PrimerSeguimiento.objects.exists()


@pytest.mark.django_db
def test_create_asignado_sigue_siendo_el_primer_seguimiento(comedor, territorial):
    """Compatibilidad con los llamadores existentes."""
    seg = PrimerSeguimientoService.create_asignado(
        comedor.id, TERRITORIAL_JSON % territorial.id
    )

    assert (seg.tipo, seg.numero_orden) == ("primer", 1)
