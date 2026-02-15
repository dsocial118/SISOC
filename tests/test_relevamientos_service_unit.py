"""Tests for relevamientos service helpers and update flows."""

from contextlib import nullcontext
from types import SimpleNamespace

import pytest

from relevamientos import service as module

pytestmark = pytest.mark.django_db


def test_update_comedor_and_separate_string(mocker):
    """update_comedor should map geo fields and numeric conversions safely."""
    prov = SimpleNamespace()
    mun = SimpleNamespace()
    loc = SimpleNamespace()
    comedor = SimpleNamespace(
        provincia=None,
        municipio=None,
        localidad=None,
        numero=1,
        calle="x",
        entre_calle_1="",
        entre_calle_2="",
        barrio="",
        codigo_postal=0,
        partido="",
        manzana="",
        piso="",
        departamento="",
        lote="",
        comienzo=None,
        save=mocker.Mock(),
        id=7,
    )
    mocker.patch("relevamientos.service.Provincia.objects.get", return_value=prov)
    mocker.patch("relevamientos.service.Municipio.objects.get_or_create", return_value=(mun, True))
    mocker.patch("relevamientos.service.Localidad.objects.get_or_create", return_value=(loc, True))
    mocker.patch("relevamientos.service.convert_string_to_int", side_effect=lambda x: int(str(x)) if str(x).isdigit() else None)

    cid = module.RelevamientoService.update_comedor(
        {
            "provincia": "P",
            "municipio": "M",
            "localidad": "L",
            "numero": "12",
            "codigo_postal": "7600",
            "comienzo": "01/2020",
        },
        comedor,
    )
    assert cid == 7
    assert comedor.save.called

    assert module.RelevamientoService.separate_string([]) == "-"
    assert module.RelevamientoService.separate_string(["A"]) == "A"
    assert module.RelevamientoService.separate_string(["A", "B"]) == "A y B"


def test_create_pendiente_and_update_territorial(mocker):
    """Territorial assignment should create pending records and trigger async sync."""
    request = SimpleNamespace(POST={"territorial": '{"gestionar_uid":"u","nombre":"N"}'})
    comedor = SimpleNamespace()
    mocker.patch("relevamientos.service.get_object_or_404", return_value=comedor)

    created = SimpleNamespace(territorial_uid=None, territorial_nombre=None, estado="Pendiente", save=mocker.Mock())
    mocker.patch("relevamientos.service.Relevamiento", return_value=created)
    out = module.RelevamientoService.create_pendiente(request, comedor_id=1)
    assert out is created
    assert out.estado == "Visita pendiente"

    rel = SimpleNamespace(id=5, territorial_uid=None, territorial_nombre=None, estado="Pendiente", save=mocker.Mock())
    mocker.patch("relevamientos.service.Relevamiento.objects.get", return_value=rel)
    mocker.patch("relevamientos.service.build_relevamiento_payload", return_value={"x": 1})
    starter = mocker.patch("relevamientos.service.AsyncSendRelevamientoToGestionar")

    req_edit = SimpleNamespace(POST={"relevamiento_id": "5", "territorial_editar": '{"gestionar_uid":"u2","nombre":"N2"}'})
    out2 = module.RelevamientoService.update_territorial(req_edit)
    assert out2 is rel
    assert starter.called


def test_populate_data_helpers(mocker):
    """Populate helpers should delegate field transformation through populate_data."""
    mocker.patch("relevamientos.service.populate_data", side_effect=lambda data, _tr: {**data, "_ok": True})

    a = module.RelevamientoService.populate_cocina_data({"heladera": "si"})
    b = module.RelevamientoService.populate_colaboradores_data({"cantidad_colaboradores": "1"})
    c = module.RelevamientoService.populate_recursos_data({"recibe_otros": "si"})
    d = module.RelevamientoService.populate_espacio_prestacion_data({"espacio_equipado": "si"})

    assert a["_ok"] and b["_ok"] and c["_ok"] and d["_ok"]


def test_create_or_update_cocina_espacio_and_colaboradores(mocker):
    """Entity builders should create/update instances and return them."""
    mocker.patch.object(module.RelevamientoService, "populate_cocina_data", return_value={"abastecimiento_combustible": "Gas"})
    qs = SimpleNamespace(exists=lambda: True)
    mocker.patch("relevamientos.service.TipoCombustible.objects.filter", return_value=qs)
    mocker.patch("relevamientos.service.EspacioCocina.objects.create", return_value=SimpleNamespace(abastecimiento_combustible=SimpleNamespace(set=mocker.Mock()), save=mocker.Mock()))
    c = module.RelevamientoService.create_or_update_cocina({"abastecimiento_combustible": "Gas"})
    assert c is not None

    mocker.patch.object(module.RelevamientoService, "create_or_update_cocina", return_value="coc")
    mocker.patch.object(module.RelevamientoService, "create_or_update_espacio_prestacion", return_value="pre")
    mocker.patch("relevamientos.service.TipoEspacio.objects.get", return_value="tipo")
    mocker.patch("relevamientos.service.Espacio.objects.create", return_value=SimpleNamespace())
    esp = module.RelevamientoService.create_or_update_espacio({"cocina": {}, "prestacion": {}, "tipo_espacio_fisico": "Salon"})
    assert esp is not None

    mocker.patch.object(module.RelevamientoService, "populate_colaboradores_data", return_value={"x": 1})
    mocker.patch("relevamientos.service.Colaboradores.objects.create", return_value=SimpleNamespace())
    col = module.RelevamientoService.create_or_update_colaboradores({"x": 1})
    assert col is not None


def test_create_or_update_recursos_and_compras(mocker):
    """Recursos and compras builders should manage scalar and many-to-many fields."""
    rec_inst = SimpleNamespace(
        recursos_donaciones_particulares=SimpleNamespace(set=mocker.Mock()),
        recursos_estado_nacional=SimpleNamespace(set=mocker.Mock()),
        recursos_estado_provincial=SimpleNamespace(set=mocker.Mock()),
        recursos_estado_municipal=SimpleNamespace(set=mocker.Mock()),
        recursos_otros=SimpleNamespace(set=mocker.Mock()),
        save=mocker.Mock(),
    )
    mocker.patch.object(module.RelevamientoService, "populate_recursos_data", return_value={"recibe_otros": True, "recursos_otros": [1]})
    mocker.patch("relevamientos.service.FuenteRecursos.objects.create", return_value=rec_inst)
    rec = module.RelevamientoService.create_or_update_recursos({"recibe_otros": True, "recursos_otros": [1]})
    assert rec is rec_inst

    mocker.patch.object(module.RelevamientoService, "populate_compras_data", return_value={"k": 1})
    mocker.patch("relevamientos.service.FuenteCompras.objects.create", return_value=SimpleNamespace())
    cmp = module.RelevamientoService.create_or_update_compras({"k": 1})
    assert cmp is not None
