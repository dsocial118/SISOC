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
    mocker.patch(
        "relevamientos.service.Municipio.objects.get_or_create",
        return_value=(mun, True),
    )
    mocker.patch(
        "relevamientos.service.Localidad.objects.get_or_create",
        return_value=(loc, True),
    )
    mocker.patch(
        "relevamientos.service.convert_string_to_int",
        side_effect=lambda x: int(str(x)) if str(x).isdigit() else None,
    )

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
    request = SimpleNamespace(
        POST={"territorial": '{"gestionar_uid":"u","nombre":"N"}'}
    )
    comedor = SimpleNamespace()
    mocker.patch("relevamientos.service.get_object_or_404", return_value=comedor)

    created = SimpleNamespace(
        territorial_uid=None,
        territorial_nombre=None,
        estado="Pendiente",
        save=mocker.Mock(),
    )
    mocker.patch("relevamientos.service.Relevamiento", return_value=created)
    out = module.RelevamientoService.create_pendiente(request, comedor_id=1)
    assert out is created
    assert out.estado == "Visita pendiente"

    rel = SimpleNamespace(
        id=5,
        territorial_uid=None,
        territorial_nombre=None,
        estado="Pendiente",
        save=mocker.Mock(),
    )
    mocker.patch("relevamientos.service.Relevamiento.objects.get", return_value=rel)
    mocker.patch(
        "relevamientos.service.build_relevamiento_payload", return_value={"x": 1}
    )
    starter = mocker.patch("relevamientos.service.AsyncSendRelevamientoToGestionar")

    req_edit = SimpleNamespace(
        POST={
            "relevamiento_id": "5",
            "territorial_editar": '{"gestionar_uid":"u2","nombre":"N2"}',
        }
    )
    out2 = module.RelevamientoService.update_territorial(req_edit)
    assert out2 is rel
    assert starter.called


def test_populate_data_helpers(mocker):
    """Populate helpers should delegate field transformation through populate_data."""
    mocker.patch(
        "relevamientos.service.populate_data",
        side_effect=lambda data, _tr: {**data, "_ok": True},
    )

    a = module.RelevamientoService.populate_cocina_data({"heladera": "si"})
    b = module.RelevamientoService.populate_colaboradores_data(
        {"cantidad_colaboradores": "1"}
    )
    c = module.RelevamientoService.populate_recursos_data({"recibe_otros": "si"})
    d = module.RelevamientoService.populate_espacio_prestacion_data(
        {"espacio_equipado": "si"}
    )

    assert a["_ok"] and b["_ok"] and c["_ok"] and d["_ok"]


def test_create_or_update_cocina_espacio_and_colaboradores(mocker):
    """Entity builders should create/update instances and return them."""
    mocker.patch.object(
        module.RelevamientoService,
        "populate_cocina_data",
        return_value={"abastecimiento_combustible": "Gas"},
    )
    qs = SimpleNamespace(exists=lambda: True)
    mocker.patch(
        "relevamientos.service.TipoCombustible.objects.filter", return_value=qs
    )
    mocker.patch(
        "relevamientos.service.EspacioCocina.objects.create",
        return_value=SimpleNamespace(
            abastecimiento_combustible=SimpleNamespace(set=mocker.Mock()),
            save=mocker.Mock(),
        ),
    )
    c = module.RelevamientoService.create_or_update_cocina(
        {"abastecimiento_combustible": "Gas"}
    )
    assert c is not None

    mocker.patch.object(
        module.RelevamientoService, "create_or_update_cocina", return_value="coc"
    )
    mocker.patch.object(
        module.RelevamientoService,
        "create_or_update_espacio_prestacion",
        return_value="pre",
    )
    mocker.patch("relevamientos.service.TipoEspacio.objects.get", return_value="tipo")
    mocker.patch(
        "relevamientos.service.Espacio.objects.create", return_value=SimpleNamespace()
    )
    esp = module.RelevamientoService.create_or_update_espacio(
        {"cocina": {}, "prestacion": {}, "tipo_espacio_fisico": "Salon"}
    )
    assert esp is not None

    mocker.patch.object(
        module.RelevamientoService, "populate_colaboradores_data", return_value={"x": 1}
    )
    mocker.patch(
        "relevamientos.service.Colaboradores.objects.create",
        return_value=SimpleNamespace(),
    )
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
    mocker.patch.object(
        module.RelevamientoService,
        "populate_recursos_data",
        return_value={"recibe_otros": True, "recursos_otros": [1]},
    )
    mocker.patch(
        "relevamientos.service.FuenteRecursos.objects.create", return_value=rec_inst
    )
    rec = module.RelevamientoService.create_or_update_recursos(
        {"recibe_otros": True, "recursos_otros": [1]}
    )
    assert rec is rec_inst

    mocker.patch.object(
        module.RelevamientoService, "populate_compras_data", return_value={"k": 1}
    )
    mocker.patch(
        "relevamientos.service.FuenteCompras.objects.create",
        return_value=SimpleNamespace(),
    )
    cmp = module.RelevamientoService.create_or_update_compras({"k": 1})
    assert cmp is not None


def test_get_relevamiento_detail_object_and_not_found(mocker):
    """Detail object should normalize string fields and return None on missing record."""

    class _ValuesChain:
        def values(self, *args, **kwargs):
            return self

        def get(self, **kwargs):
            return {"excepcion__adjuntos": "u", "imagenes": "img"}

    mocker.patch(
        "relevamientos.service.Relevamiento.objects.prefetch_related",
        return_value=_ValuesChain(),
    )

    detail = module.RelevamientoService.get_relevamiento_detail_object(1)
    assert detail["excepcion__adjuntos"] == ["u"]
    assert detail["imagenes"] == ["img"]

    mocker.patch(
        "relevamientos.service.Relevamiento.objects.prefetch_related",
        return_value=SimpleNamespace(
            values=lambda *a, **k: SimpleNamespace(
                get=mocker.Mock(side_effect=module.Relevamiento.DoesNotExist())
            )
        ),
    )
    assert module.RelevamientoService.get_relevamiento_detail_object(999) is None


def test_create_or_update_funcionamiento_create_and_update(mocker):
    """Funcionamiento should parse inputs and support create and update flows."""
    modalidad_qs = SimpleNamespace(first=lambda: "mod")
    mocker.patch(
        "relevamientos.service.TipoModalidadPrestacion.objects.filter",
        return_value=modalidad_qs,
    )
    mocker.patch("relevamientos.service.convert_to_boolean", return_value=True)
    created = SimpleNamespace()
    mocker.patch(
        "relevamientos.service.FuncionamientoPrestacion.objects.create",
        return_value=created,
    )

    out = module.RelevamientoService.create_or_update_funcionamiento(
        {
            "modalidad_prestacion": "  M ",
            "servicio_por_turnos": "si",
            "cantidad_turnos": "2",
        }
    )
    assert out is created

    assigner = mocker.patch(
        "relevamientos.service.assign_values_to_instance", return_value="updated"
    )
    out2 = module.RelevamientoService.create_or_update_funcionamiento(
        {
            "modalidad_prestacion": "",
            "servicio_por_turnos": "no",
            "cantidad_turnos": "",
        },
        funcionamiento_instance=SimpleNamespace(),
    )
    assert out2 == "updated"
    assert assigner.called


def test_create_or_update_punto_entregas_and_prestacion_flows(mocker):
    """Punto entregas and prestación should apply parsing and persist properly."""
    mocker.patch.object(
        module.RelevamientoService,
        "populate_punto_entregas_data",
        return_value={"frecuencia_recepcion_mercaderias": "Semanal, Mensual", "x": 1},
    )
    freq_qs = SimpleNamespace(exists=lambda: True)
    mocker.patch(
        "relevamientos.service.TipoFrecuenciaBolsones.objects.filter",
        return_value=freq_qs,
    )
    punto_instance = SimpleNamespace(
        frecuencia_recepcion_mercaderias=SimpleNamespace(set=mocker.Mock()),
        save=mocker.Mock(),
    )
    mocker.patch(
        "relevamientos.service.PuntoEntregas.objects.create",
        return_value=punto_instance,
    )
    out = module.RelevamientoService.create_or_update_punto_entregas({"k": 1})
    assert out is punto_instance

    mocker.patch.object(
        module.RelevamientoService,
        "populate_prestacion_data",
        return_value={"lunes_almuerzo_actual": 5},
    )
    mocker.patch(
        "relevamientos.service.Prestacion.objects.create",
        return_value=SimpleNamespace(),
    )
    assert module.RelevamientoService.create_or_update_prestacion({"k": 1}) is not None


def test_populate_prestacion_data_converts_day_meals(mocker):
    """populate_prestacion_data should convert known day/meal keys to integers."""
    converted = mocker.patch(
        "relevamientos.service.convert_string_to_int", side_effect=lambda x: int(x)
    )
    data = {"lunes_desayuno_actual": "1", "martes_cena_espera": "2"}
    out_data = module.RelevamientoService.populate_prestacion_data(data)
    assert out_data["lunes_desayuno_actual"] == 1
    assert out_data["martes_cena_espera"] == 2
    assert converted.call_count >= 2


def test_create_or_update_responsable_referente_and_excepcion(mocker):
    """Responsable/referente and excepción flows should resolve entities and update links."""
    responsable = SimpleNamespace(id=10, save=mocker.Mock())
    referente = SimpleNamespace(id=11, save=mocker.Mock())

    mocker.patch(
        "relevamientos.service.Referente.objects.filter",
        side_effect=[
            SimpleNamespace(last=lambda: responsable),
            SimpleNamespace(last=lambda: referente),
        ],
    )
    comedor = SimpleNamespace(referente=None, save=mocker.Mock())
    mocker.patch(
        "relevamientos.service.Relevamiento.objects.get",
        return_value=SimpleNamespace(comedor=comedor),
    )

    rid, fid = module.RelevamientoService.create_or_update_responsable_y_referente(
        False,
        {"documento": "1", "nombre": "R"},
        {"documento": "2", "nombre": "F"},
        sisoc_id=99,
    )
    assert rid == 10
    assert fid == 11
    assert comedor.save.called

    mocker.patch.object(
        module.RelevamientoService,
        "populate_excepcion_data",
        return_value={"motivo": "M", "adjuntos": ["u"]},
    )
    mocker.patch(
        "relevamientos.service.Excepcion.objects.create", return_value=SimpleNamespace()
    )
    assert (
        module.RelevamientoService.create_or_update_excepcion({"motivo": "x"})
        is not None
    )


def test_populate_excepcion_data_parses_motivo_and_adjuntos(mocker):
    """populate_excepcion_data should map motivo object and split attachments."""
    mocker.patch("relevamientos.service.get_object_or_none", return_value="motivo_obj")
    parsed = module.RelevamientoService.populate_excepcion_data(
        {"motivo": "M", "adjuntos": "a, b"}
    )
    assert parsed["motivo"] == "motivo_obj"
    assert parsed["adjuntos"] == ["a", "b"]


def test_populate_relevamiento_and_update_territorial_without_data(mocker):
    """populate_relevamiento and update_territorial should handle default branches."""
    rel = SimpleNamespace(save=mocker.Mock())
    relevamiento_form = SimpleNamespace(
        save=lambda commit=False: rel,
        cleaned_data={"responsable_es_referente": "True"},
        data={"x": 1},
    )
    espacio = SimpleNamespace(save=mocker.Mock())
    extra_forms = {
        "funcionamiento_form": SimpleNamespace(save=lambda: "fun"),
        "espacio_form": SimpleNamespace(save=lambda commit=False: espacio),
        "espacio_cocina_form": SimpleNamespace(save=lambda commit=True: "coc"),
        "espacio_prestacion_form": SimpleNamespace(save=lambda commit=True: "prep"),
        "colaboradores_form": SimpleNamespace(save=lambda: "col"),
        "recursos_form": SimpleNamespace(save=lambda: "rec"),
        "anexo_form": SimpleNamespace(save=lambda: "an"),
        "compras_form": SimpleNamespace(save=lambda: "comp"),
        "prestacion_form": SimpleNamespace(save=lambda: "pres"),
        "referente_form": SimpleNamespace(save=lambda: "ref"),
        "punto_entregas_form": SimpleNamespace(save=lambda: "punto"),
    }
    mocker.patch("relevamientos.service.timezone.now", return_value="now")
    out = module.RelevamientoService.populate_relevamiento(
        relevamiento_form, extra_forms
    )
    assert out is rel
    assert rel.responsable_es_referente is True

    rel2 = SimpleNamespace(
        territorial_nombre="x",
        territorial_uid="y",
        estado="Visita pendiente",
        id=2,
        save=mocker.Mock(),
    )
    mocker.patch("relevamientos.service.Relevamiento.objects.get", return_value=rel2)
    mocker.patch(
        "relevamientos.service.build_relevamiento_payload", return_value={"k": 1}
    )
    starter = mocker.patch("relevamientos.service.AsyncSendRelevamientoToGestionar")
    req = SimpleNamespace(POST={"relevamiento_id": "2", "territorial_editar": ""})
    out2 = module.RelevamientoService.update_territorial(req)
    assert out2 is rel2
    assert rel2.estado == "Pendiente"
    assert starter.called


def test_create_or_update_anexo_and_populate_helpers(mocker):
    """Anexo/punto/compras populate helpers should transform and persist data."""
    mocker.patch(
        "relevamientos.service.populate_data",
        side_effect=lambda data, _tr: {**data, "ok": True},
    )
    mocker.patch("relevamientos.service.convert_string_to_int", return_value=3)
    parsed = module.RelevamientoService.populate_anexo_data(
        {"veces_recibio_insumos_2024": "3"}
    )
    assert parsed["ok"] is True
    assert parsed["veces_recibio_insumos_2024"] == 3

    mocker.patch(
        "relevamientos.service.Anexo.objects.create",
        return_value=SimpleNamespace(),
    )
    mocker.patch.object(
        module.RelevamientoService, "populate_anexo_data", return_value={"a": 1}
    )
    assert module.RelevamientoService.create_or_update_anexo({"a": 1}) is not None

    p = module.RelevamientoService.populate_punto_entregas_data(
        {"existe_punto_entregas": "Y"}
    )
    c = module.RelevamientoService.populate_compras_data({"almacen_cercano": "N"})
    assert p["ok"] and c["ok"]


def test_responsable_referente_create_and_self_reference(mocker):
    """When responsable_es_referente is true, both IDs should point to the same record."""
    mocker.patch(
        "relevamientos.service.Referente.objects.filter",
        return_value=SimpleNamespace(last=lambda: None),
    )
    created = SimpleNamespace(id=20)
    mocker.patch("relevamientos.service.Referente.objects.create", return_value=created)

    rid, fid = module.RelevamientoService.create_or_update_responsable_y_referente(
        True,
        {"documento": "1", "nombre": "R"},
        {},
        sisoc_id=None,
    )
    assert rid == 20
    assert fid == 20


@pytest.mark.parametrize(
    "method_name, patch_target",
    [
        ("create_or_update_compras", "populate_compras_data"),
        ("create_or_update_anexo", "populate_anexo_data"),
        ("create_or_update_punto_entregas", "populate_punto_entregas_data"),
        ("create_or_update_prestacion", "populate_prestacion_data"),
        ("create_or_update_excepcion", "populate_excepcion_data"),
    ],
)
def test_builder_exception_paths_raise(mocker, method_name, patch_target):
    """Builder methods should log and re-raise on unexpected internal errors."""
    mocker.patch.object(
        module.RelevamientoService, patch_target, side_effect=RuntimeError("boom")
    )
    method = getattr(module.RelevamientoService, method_name)
    with pytest.raises(RuntimeError, match="boom"):
        method({"x": 1})
