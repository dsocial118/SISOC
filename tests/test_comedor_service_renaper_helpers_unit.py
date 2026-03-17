"""Tests for test comedor service renaper helpers unit."""

from contextlib import nullcontext
from datetime import date, datetime
from types import SimpleNamespace

import pytest

from comedores.services import comedor_service as module


class _QS(list):
    def filter(self, **kwargs):
        out = list(self)
        if "provincia" in kwargs:
            prov = kwargs["provincia"]
            out = [x for x in out if getattr(x, "provincia", None) == prov]
        if "municipio" in kwargs:
            mun = kwargs["municipio"]
            out = [x for x in out if getattr(x, "municipio", None) == mun]
        if "municipio__provincia" in kwargs:
            prov = kwargs["municipio__provincia"]
            out = [
                x
                for x in out
                if getattr(getattr(x, "municipio", None), "provincia", None) == prov
            ]
        return _QS(out)


class _ComedoresListQS:
    """QS falso para caracterizar encadenamiento de filtros de listado."""

    def __init__(self):
        self.calls = []

    def select_related(self, *args, **_kwargs):
        self.calls.append(("select_related", args))
        return self

    def annotate(self, **kwargs):
        self.calls.append(("annotate", tuple(kwargs.keys())))
        return self

    def values(self, *args):
        self.calls.append(("values", args))
        return self

    def order_by(self, *args):
        self.calls.append(("order_by", args))
        return self

    def filter(self, *args, **kwargs):
        self.calls.append(("filter", args, kwargs))
        return self

    def none(self):
        self.calls.append(("none",))
        return self


class _NominaQS:
    def __init__(self, resumen):
        self.resumen = resumen
        self.calls = []

    def select_related(self, *args):
        self.calls.append(("select_related", args))
        return self

    def annotate(self, **kwargs):
        self.calls.append(("annotate", tuple(kwargs.keys())))
        return self

    def aggregate(self, **kwargs):
        self.calls.append(("aggregate", tuple(kwargs.keys())))
        return self.resumen

    def only(self, *args):
        self.calls.append(("only", args))
        return self


class _RelevamientoLookupQS:
    def __init__(self, first_result):
        self.first_result = first_result
        self.calls = []

    def filter(self, **kwargs):
        self.calls.append(("filter", kwargs))
        return self

    def order_by(self, *args):
        self.calls.append(("order_by", args))
        return self

    def only(self, *args):
        self.calls.append(("only", args))
        return self

    def first(self):
        self.calls.append(("first",))
        return self.first_result


class _RelevamientoManagerSeq:
    def __init__(self, results):
        self._results = list(results)
        self.select_related_calls = []
        self.qs_instances = []

    def select_related(self, *args):
        self.select_related_calls.append(args)
        result = self._results.pop(0) if self._results else None
        qs = _RelevamientoLookupQS(result)
        self.qs_instances.append(qs)
        return qs


def test_parse_fecha_and_text_normalizers():
    assert module.ComedorService._parse_fecha_renaper("2024-01-20") == date(2024, 1, 20)
    assert module.ComedorService._parse_fecha_renaper("20/01/2024") == date(2024, 1, 20)
    assert module.ComedorService._parse_fecha_renaper("20240120") == date(2024, 1, 20)
    assert module.ComedorService._parse_fecha_renaper(
        datetime(2024, 1, 20, 10, 0)
    ) == datetime(2024, 1, 20, 10, 0)
    assert module.ComedorService._parse_fecha_renaper("invalid") is None

    assert module.ComedorService._replace_number_words("uno y dos") == "1 y dos"
    assert module.ComedorService._to_camel_case("  juAN   peREZ ") == "Juan Perez"
    assert (
        module.ComedorService._apply_geo_alias("caba")
        == "ciudad autonoma de buenos aires"
    )
    assert module.ComedorService._normalize_geo_value("Veintidós - CABA") == "22 caba"
    assert module.ComedorService._normalize_text("Árbol_Grande") == "arbol grande"


def test_match_geo_mapear_and_nacionalidad(mocker):
    prov = SimpleNamespace(pk=1, nombre="Buenos Aires")
    mun = SimpleNamespace(pk=2, nombre="General Pueyrredon", provincia=prov)
    loc = SimpleNamespace(pk=3, nombre="Mar del Plata", municipio=mun)

    mocker.patch(
        "comedores.services.comedor_service.impl.Provincia.objects.all",
        return_value=_QS([prov]),
    )
    mocker.patch(
        "comedores.services.comedor_service.impl.Municipio.objects.all",
        return_value=_QS([mun]),
    )
    mocker.patch(
        "comedores.services.comedor_service.impl.Localidad.objects.all",
        return_value=_QS([loc]),
    )

    mapped = module.ComedorService._mapear_ubicacion_desde_renaper(
        {
            "provincia_api": "buenos aires",
            "municipio_api": "general pueyrredon",
            "localidad_api": "mar del plata",
        }
    )
    assert mapped["provincia"] is prov
    assert mapped["municipio"] is mun
    assert mapped["localidad"] is loc

    nac = SimpleNamespace(pk=8, nacionalidad="Argentina")
    mocker.patch(
        "comedores.services.comedor_service.impl.Nacionalidad.objects.all",
        return_value=[nac],
    )
    assert module.ComedorService._match_nacionalidad("argentina") is nac


def test_consultar_renaper_and_build_data(mocker):
    mocker.patch(
        "comedores.services.comedor_service.impl.consultar_datos_renaper",
        side_effect=[
            {"success": False, "error": "x"},
            {"success": True, "data": {"dni": "123"}},
        ],
    )
    ok = module.ComedorService._consultar_renaper_por_dni("123")
    assert ok["success"] is True

    mocker.patch(
        "comedores.services.comedor_service.impl.consultar_datos_renaper",
        side_effect=[
            {"success": False, "error": "x"},
            {"success": False, "error": "y"},
            {"success": False, "error": "z"},
        ],
    )
    fail = module.ComedorService._consultar_renaper_por_dni("123")
    assert fail["success"] is False

    mocker.patch.object(
        module.ComedorService,
        "_mapear_ubicacion_desde_renaper",
        return_value={"provincia": None, "municipio": None, "localidad": None},
    )
    mocker.patch.object(module.ComedorService, "_match_nacionalidad", return_value=None)

    data, err = module.ComedorService._build_ciudadano_data_from_renaper(
        {
            "apellido": "PEREZ",
            "nombre": "juan",
            "fecha_nacimiento": "2020-01-20",
            "dni": "12345678",
            "tipo_documento": "DNI",
            "sexo": "M",
            "calle": "A",
            "altura": 12,
            "codigo_postal": 7600,
        },
        "12345678",
    )
    assert err is None
    assert data["apellido"] == "Perez"
    assert data["documento"] == 12345678

    data2, err2 = module.ComedorService._build_ciudadano_data_from_renaper({}, "abc")
    assert data2 is None
    assert err2


def test_obtener_datos_ciudadano_desde_renaper_and_crear(mocker):
    bad = module.ComedorService.obtener_datos_ciudadano_desde_renaper("12")
    assert bad["success"] is False

    mocker.patch(
        "comedores.services.comedor_service.impl.consultar_datos_renaper",
        return_value={"success": False, "error": "no"},
    )
    out = module.ComedorService.obtener_datos_ciudadano_desde_renaper(
        "12345678", sexo="M"
    )
    assert out["success"] is False

    mocker.patch.object(
        module.ComedorService,
        "_consultar_renaper_por_dni",
        return_value={
            "success": True,
            "data": {
                "apellido": "A",
                "nombre": "B",
                "fecha_nacimiento": "2020-01-01",
                "dni": "12345678",
            },
            "datos_api": {"k": 1},
        },
    )
    mocker.patch.object(
        module.ComedorService,
        "_build_ciudadano_data_from_renaper",
        return_value=({"documento": 12345678}, None),
    )
    ok = module.ComedorService.obtener_datos_ciudadano_desde_renaper("12345678")
    assert ok["success"] is True

    existing = SimpleNamespace(pk=1)
    mocker.patch(
        "comedores.services.comedor_service.impl.Ciudadano.objects.filter",
        return_value=SimpleNamespace(first=lambda: existing),
    )
    ex = module.ComedorService.crear_ciudadano_desde_renaper("12345678")
    assert ex["created"] is False

    mocker.patch(
        "comedores.services.comedor_service.impl.Ciudadano.objects.filter",
        return_value=SimpleNamespace(first=lambda: None),
    )
    mocker.patch.object(
        module.ComedorService,
        "obtener_datos_ciudadano_desde_renaper",
        return_value={"success": True, "data": {"documento": 123}, "datos_api": {}},
    )
    created = SimpleNamespace(pk=2)
    mocker.patch(
        "comedores.services.comedor_service.impl.Ciudadano.objects.create",
        return_value=created,
    )
    new = module.ComedorService.crear_ciudadano_desde_renaper(
        "12345678", user=SimpleNamespace(is_authenticated=True)
    )
    assert new["created"] is True


def test_agregar_nomina_and_crear_y_agregar(mocker):
    mocker.patch(
        "comedores.services.comedor_service.impl.get_object_or_404",
        return_value=SimpleNamespace(pk=1),
    )
    mocker.patch(
        "comedores.services.comedor_service.impl.Nomina.objects.filter",
        return_value=SimpleNamespace(exists=lambda: True),
    )
    ok, _msg = module.ComedorService.agregar_ciudadano_a_nomina(1, 1, user="u")
    assert ok is False

    mocker.patch(
        "comedores.services.comedor_service.impl.Nomina.objects.filter",
        return_value=SimpleNamespace(exists=lambda: False),
    )
    mocker.patch(
        "comedores.services.comedor_service.impl.transaction.atomic",
        return_value=nullcontext(),
    )
    mocker.patch("comedores.services.comedor_service.impl.Nomina.objects.create")
    ok2, _msg2 = module.ComedorService.agregar_ciudadano_a_nomina(1, 1, user="u")
    assert ok2 is True

    c = SimpleNamespace(id=9, delete=mocker.Mock())
    mocker.patch(
        "comedores.services.comedor_service.impl.Ciudadano.objects.create",
        return_value=c,
    )
    mocker.patch.object(
        module.ComedorService, "agregar_ciudadano_a_nomina", return_value=(False, "x")
    )
    ok3, _msg3 = module.ComedorService.crear_ciudadano_y_agregar_a_nomina.__wrapped__(
        {}, 1, "u", None, None
    )
    assert ok3 is False
    assert c.delete.called


def test_timeline_context_helpers_cover_both_states():
    admision_enviada = SimpleNamespace(
        enviado_acompaniamiento=True, creado="2024-01-01"
    )
    qs = SimpleNamespace(
        filter=lambda **kwargs: SimpleNamespace(
            order_by=lambda *args, **kwargs: SimpleNamespace(
                first=lambda: admision_enviada
            )
        )
    )

    ctx = module.ComedorService.get_admision_timeline_context(qs)
    assert ctx["timeline_admision_step_class"] == "step completed"
    assert ctx["timeline_connector_class"] == "connector completed"

    ctx2 = module.ComedorService.get_admision_timeline_context_from_admision(
        SimpleNamespace(enviado_acompaniamiento=False, creado="2024-02-02")
    )
    assert ctx2["timeline_admision_step_class"] == "step active"
    assert ctx2["timeline_connector_class"] == "connector"


def test_asignar_dupla_y_delete_images(mocker):
    comedor = SimpleNamespace(dupla_id=None, estado=None, save=mocker.Mock())
    mocker.patch(
        "comedores.services.comedor_service.impl.Comedor.objects.get",
        return_value=comedor,
    )

    out = module.ComedorService.asignar_dupla_a_comedor(5, 10)
    assert out is comedor
    assert comedor.dupla_id == 5
    assert comedor.estado == "Asignado a Dupla Técnica"
    comedor.save.assert_called_once()

    filtered = SimpleNamespace(delete=mocker.Mock())
    filter_mock = mocker.patch(
        "comedores.services.comedor_service.impl.ImagenComedor.objects.filter",
        return_value=filtered,
    )
    module.ComedorService.delete_images(
        {
            "imagen_ciudadano-borrar-12": "on",
            "otra_key": "x",
            "imagen_ciudadano-borrar-34": "on",
        }
    )
    filter_mock.assert_called_once_with(id__in=["12", "34"])
    filtered.delete.assert_called_once()


def test_delete_legajo_photo_handles_delete_exception(mocker):
    comedor = SimpleNamespace(
        pk=77,
        foto_legajo=SimpleNamespace(name="a/b.jpg"),
        save=mocker.Mock(),
    )
    mocker.patch(
        "comedores.services.comedor_service.impl.default_storage.delete",
        side_effect=RuntimeError("boom"),
    )
    log_mock = mocker.patch("comedores.services.comedor_service.impl.logger.exception")

    module.ComedorService.delete_legajo_photo({"foto_legajo_borrar": "1"}, comedor)

    assert comedor.foto_legajo is None
    comedor.save.assert_called_once_with(update_fields=["foto_legajo"])
    assert log_mock.called


def test_get_ubicaciones_ids_and_referente_create_update(mocker):
    mocker.patch(
        "comedores.services.comedor_service.impl.get_id_by_nombre",
        side_effect=[1, 2, 3],
    )
    data = module.ComedorService.get_ubicaciones_ids(
        {"provincia": "A", "municipio": "B", "localidad": "C"}
    )
    assert data == {"provincia": 1, "municipio": 2, "localidad": 3}

    mocker.patch(
        "comedores.services.comedor_service.impl.normalize_field",
        side_effect=lambda value, _char: value,
    )
    created = SimpleNamespace(pk=1)
    mocker.patch(
        "comedores.services.comedor_service.impl.Referente.objects.create",
        return_value=created,
    )
    out = module.ComedorService.create_or_update_referente(
        {"referente": {"nombre": "Ana", "celular": "11-2222", "documento": "10.111"}}
    )
    assert out is created

    existing = SimpleNamespace(save=mocker.Mock())
    out2 = module.ComedorService.create_or_update_referente(
        {"referente": {"nombre": "Luis", "celular": "123", "documento": "321"}},
        referente_instance=existing,
    )
    assert out2 is existing
    assert existing.nombre == "Luis"
    existing.save.assert_called_once()


def test_create_imagenes_valid_and_invalid(mocker):
    valid_form = SimpleNamespace(is_valid=lambda: True, save=lambda: "ok")
    invalid_form = SimpleNamespace(is_valid=lambda: False, errors={"imagen": ["x"]})
    form_ctor = mocker.patch(
        "comedores.services.comedor_service.impl.ImagenComedorForm",
        side_effect=[valid_form, invalid_form],
    )

    assert module.ComedorService.create_imagenes("img1", 9) == "ok"
    assert module.ComedorService.create_imagenes("img2", 9) == {"imagen": ["x"]}
    assert form_ctor.call_count == 2


def test_relevamiento_resumen_presupuestos_and_aprobadas(mocker):
    assert module.ComedorService.get_relevamiento_resumen([]) is None

    r1 = SimpleNamespace(estado="Pendiente")
    r2 = SimpleNamespace(estado="Finalizado")
    assert module.ComedorService.get_relevamiento_resumen([r1, r2]) is r2
    assert module.ComedorService.get_relevamiento_resumen([r1]) is r1

    prestacion = SimpleNamespace()
    for dia in [
        "lunes",
        "martes",
        "miercoles",
        "jueves",
        "viernes",
        "sabado",
        "domingo",
    ]:
        setattr(prestacion, f"{dia}_desayuno_actual", 1)
        setattr(prestacion, f"{dia}_almuerzo_actual", 2)
        setattr(prestacion, f"{dia}_merienda_actual", 3)
        setattr(prestacion, f"{dia}_cena_actual", 4)
        setattr(prestacion, f"{dia}_merienda_reforzada_actual", 1)

    mocker.patch(
        "comedores.services.comedor_service.impl.preload_valores_comida_cache",
        return_value={"cena": 10, "desayuno": 20, "almuerzo": 30, "merienda": 40},
    )
    result = module.ComedorService.get_presupuestos(
        1,
        relevamientos_prefetched=[
            SimpleNamespace(prestacion=prestacion, estado="Finalizado")
        ],
    )
    assert result[0] > 0
    assert result[1] == 280
    assert result[2] == 140
    assert result[3] == 420
    assert result[4] == 840

    informe = SimpleNamespace(
        aprobadas_desayuno_lunes="2",
        aprobadas_desayuno_martes=None,
        aprobadas_almuerzo_lunes="x",
        aprobadas_almuerzo_martes=3,
        aprobadas_merienda_lunes=1,
        aprobadas_cena_lunes=4,
    )
    apro = module.ComedorService.get_prestaciones_aprobadas_por_tipo(informe)
    assert apro["desayuno"] == 2
    assert apro["almuerzo"] == 3
    assert apro["merienda"] == 1
    assert apro["cena"] == 4
    assert (
        module.ComedorService.calcular_monto_prestacion_mensual_por_aprobadas(apro)
        == (3 + 4) * 763 + (2 + 1) * 383
    )
    assert (
        module.ComedorService.calcular_monto_prestacion_mensual_por_aprobadas(None)
        is None
    )


def test_post_comedor_relevamiento_branches(mocker):
    comedor = SimpleNamespace(id=22)
    req = SimpleNamespace(POST={"territorial": "1"})
    mocker.patch("comedores.services.comedor_service.impl.reverse", return_value="/r/1")
    ok_redirect = mocker.patch(
        "comedores.services.comedor_service.impl.redirect",
        side_effect=lambda *args, **kwargs: (args, kwargs),
    )
    mocker.patch(
        "comedores.services.comedor_service.impl.RelevamientoService.create_pendiente",
        return_value=SimpleNamespace(pk=9, comedor=SimpleNamespace(pk=22)),
    )
    out = module.ComedorService.post_comedor_relevamiento(req, comedor)
    assert out[0][0] == "/r/1"

    req2 = SimpleNamespace(POST={"territorial_editar": "1"})
    msg_error = mocker.patch("comedores.services.comedor_service.impl.messages.error")
    mocker.patch(
        "comedores.services.comedor_service.impl.RelevamientoService.update_territorial",
        return_value=SimpleNamespace(pk=1, comedor=None),
    )
    out2 = module.ComedorService.post_comedor_relevamiento(req2, comedor)
    assert out2[0][0] == "comedor_detalle"
    assert msg_error.called

    req3 = SimpleNamespace(POST={})
    out3 = module.ComedorService.post_comedor_relevamiento(req3, comedor)
    assert out3[0][0] == "comedor_detalle"
    assert ok_redirect.called


def test_get_presupuestos_queries_finalizado_y_fallback(mocker):
    mocker.patch(
        "comedores.services.comedor_service.impl.preload_valores_comida_cache",
        return_value={"cena": 1, "desayuno": 2, "almuerzo": 3, "merienda": 4},
    )
    prestacion = SimpleNamespace()
    setattr(prestacion, "lunes_desayuno_actual", 1)
    setattr(prestacion, "lunes_almuerzo_actual", 2)
    setattr(prestacion, "lunes_merienda_actual", 3)
    setattr(prestacion, "lunes_cena_actual", 4)
    setattr(prestacion, "lunes_merienda_reforzada_actual", 5)

    manager_finalizado = _RelevamientoManagerSeq(
        [SimpleNamespace(prestacion=prestacion, estado="Finalizado")]
    )
    mocker.patch(
        "comedores.services.comedor_service.impl.Relevamiento.objects",
        manager_finalizado,
    )
    result = module.ComedorService.get_presupuestos(77)
    assert manager_finalizado.select_related_calls == [("prestacion",)]
    assert result[:5] == (15, 4, 2, 6, 12)

    manager_fallback = _RelevamientoManagerSeq(
        [None, SimpleNamespace(prestacion=prestacion, estado="Pendiente")]
    )
    mocker.patch(
        "comedores.services.comedor_service.impl.Relevamiento.objects",
        manager_fallback,
    )
    result_fallback = module.ComedorService.get_presupuestos(88)
    assert manager_fallback.select_related_calls == [("prestacion",), ("prestacion",)]
    assert result_fallback[:5] == (15, 4, 2, 6, 12)


def test_get_presupuestos_sin_relevamientos_devuelve_ceros(mocker):
    mocker.patch(
        "comedores.services.comedor_service.impl.preload_valores_comida_cache",
        return_value={"cena": 10, "desayuno": 20, "almuerzo": 30, "merienda": 40},
    )
    mocker.patch(
        "comedores.services.comedor_service.impl.Relevamiento.objects",
        _RelevamientoManagerSeq([None, None]),
    )

    result = module.ComedorService.get_presupuestos(999)

    assert result == (0, 0, 0, 0, 0, 0)


def test_crear_admision_desde_comedor_flows(mocker):
    comedor = SimpleNamespace(pk=5)
    request = SimpleNamespace(POST={}, get_full_path=lambda: "/x")
    warn = mocker.patch("comedores.services.comedor_service.impl.messages.warning")
    err = mocker.patch("comedores.services.comedor_service.impl.messages.error")
    success = mocker.patch("comedores.services.comedor_service.impl.messages.success")
    mocker.patch("comedores.services.comedor_service.impl.messages.info")
    red = mocker.patch(
        "comedores.services.comedor_service.impl.redirect",
        side_effect=lambda *args, **kwargs: (args, kwargs),
    )
    safe = mocker.patch(
        "comedores.services.comedor_service.impl.safe_redirect", return_value="safe"
    )
    mocker.patch(
        "comedores.services.comedor_service.impl.reverse", return_value="/detalle"
    )

    out_missing = module.ComedorService.crear_admision_desde_comedor(request, comedor)
    assert out_missing[0][0] == "comedor_detalle"
    assert err.called

    request.POST = {"admision": "renovacion"}
    f = mocker.Mock()
    f.exists.return_value = False
    mocker.patch(
        "comedores.services.comedor_service.impl.Admision.objects.filter",
        return_value=f,
    )
    out_no_incorp = module.ComedorService.crear_admision_desde_comedor(request, comedor)
    assert out_no_incorp[0][0] == "comedor_detalle"

    request.POST = {"admision": "incorporacion"}
    f2 = mocker.Mock()
    f2.exists.return_value = True
    mocker.patch(
        "comedores.services.comedor_service.impl.Admision.objects.filter",
        return_value=f2,
    )
    out_dup = module.ComedorService.crear_admision_desde_comedor(request, comedor)
    assert out_dup[0][0] == "comedor_detalle"
    assert warn.called

    request.POST = {"admision": "renovacion"}
    filt = mocker.Mock()
    filt.exists.side_effect = [True]
    filt.count.return_value = 4
    mocker.patch(
        "comedores.services.comedor_service.impl.Admision.objects.filter",
        return_value=filt,
    )
    out_safe = module.ComedorService.crear_admision_desde_comedor(request, comedor)
    assert out_safe == "safe"

    request.POST = {"admision": "renovacion"}

    def _filter(*args, **kwargs):
        if kwargs.get("tipo") == "incorporacion":
            return SimpleNamespace(exists=lambda: True)
        if kwargs.get("tipo") == "renovacion" and kwargs.get("activa") is True:
            return SimpleNamespace(count=lambda: 0)
        return SimpleNamespace(exists=lambda: False)

    mocker.patch(
        "comedores.services.comedor_service.impl.Admision.objects.filter",
        side_effect=_filter,
    )
    adm = SimpleNamespace(get_tipo_display=lambda: "Renovación")
    mocker.patch(
        "comedores.services.comedor_service.impl.Admision.objects.create",
        return_value=adm,
    )
    mocker.patch(
        "comedores.services.comedor_service.impl.Hitos.objects.filter",
        return_value=SimpleNamespace(exists=lambda: False),
    )
    hitos_create = mocker.patch(
        "comedores.services.comedor_service.impl.Hitos.objects.create"
    )

    out_ok = module.ComedorService.crear_admision_desde_comedor(request, comedor)
    assert out_ok[0][0] == "comedor_detalle"
    assert hitos_create.called
    assert success.call_count >= 1


def test_get_filtered_comedores_coordinador_general_delega_filtro_avanzado(mocker):
    base_qs = _ComedoresListQS()
    mocker.patch(
        "comedores.services.comedor_service.impl.Comedor.objects",
        SimpleNamespace(select_related=lambda *_a, **_k: base_qs),
    )
    filter_mock = mocker.patch(
        "comedores.services.comedor_service.impl.COMEDOR_ADVANCED_FILTER.filter_queryset",
        return_value="filtrado-final",
    )
    mocker.patch(
        "users.services.UserPermissionService.tiene_grupo",
        return_value=True,
    )
    mocker.patch(
        "users.services.UserPermissionService.get_coordinador_duplas",
        return_value=(False, []),
    )
    mocker.patch(
        "users.services.UserPermissionService.es_tecnico_o_abogado",
        return_value=False,
    )

    req_get = {"filters": "[]"}
    user = SimpleNamespace(is_superuser=False)
    out = module.ComedorService.get_filtered_comedores(req_get, user=user)

    assert out == "filtrado-final"
    filter_mock.assert_called_once_with(base_qs, req_get)
    assert any(call[0] == "values" for call in base_qs.calls)
    assert any(call[0] == "order_by" for call in base_qs.calls)


def test_get_filtered_comedores_coordinador_sin_duplas_aplica_none(mocker):
    base_qs = _ComedoresListQS()
    mocker.patch(
        "comedores.services.comedor_service.impl.Comedor.objects",
        SimpleNamespace(select_related=lambda *_a, **_k: base_qs),
    )
    filter_mock = mocker.patch(
        "comedores.services.comedor_service.impl.COMEDOR_ADVANCED_FILTER.filter_queryset",
        return_value="filtrado-none",
    )
    mocker.patch(
        "users.services.UserPermissionService.tiene_grupo",
        return_value=False,
    )
    mocker.patch(
        "users.services.UserPermissionService.get_coordinador_duplas",
        return_value=(True, []),
    )
    mocker.patch(
        "users.services.UserPermissionService.es_tecnico_o_abogado",
        return_value=False,
    )

    out = module.ComedorService.get_filtered_comedores(
        {}, user=SimpleNamespace(is_superuser=False)
    )

    assert out == "filtrado-none"
    assert ("none",) in base_qs.calls
    filter_mock.assert_called_once_with(base_qs, {})


def test_get_filtered_comedores_tecnico_abogado_reconstruye_queryset(mocker):
    class _FakeExistsExpr:
        def __init__(self, value):
            self.value = value

        def __or__(self, other):
            return ("OR", self.value, other.value)

    base_qs = _ComedoresListQS()
    dupla_qs = _ComedoresListQS()

    class _ComedorObjects:
        def select_related(self, *_a, **_k):
            return base_qs

        def filter(self, *args, **kwargs):
            dupla_qs.calls.append(("manager_filter", args, kwargs))
            return dupla_qs

    mocker.patch("django.db.models.Exists", side_effect=lambda q: _FakeExistsExpr(q))
    mocker.patch(
        "django.db.models.OuterRef", side_effect=lambda field: f"OUTER:{field}"
    )
    mocker.patch(
        "comedores.services.comedor_service.impl.Comedor",
        SimpleNamespace(objects=_ComedorObjects(), ESTADO_GENERAL_DEFAULT="Sin estado"),
    )
    mocker.patch(
        "comedores.services.comedor_service.impl.Dupla.objects",
        SimpleNamespace(
            filter=lambda **kwargs: ("dupla_filter", tuple(sorted(kwargs.items())))
        ),
    )
    filter_mock = mocker.patch(
        "comedores.services.comedor_service.impl.COMEDOR_ADVANCED_FILTER.filter_queryset",
        return_value="filtrado-dupla",
    )
    mocker.patch(
        "users.services.UserPermissionService.tiene_grupo",
        return_value=False,
    )
    mocker.patch(
        "users.services.UserPermissionService.get_coordinador_duplas",
        return_value=(False, []),
    )
    mocker.patch(
        "users.services.UserPermissionService.es_tecnico_o_abogado",
        return_value=True,
    )

    out = module.ComedorService.get_filtered_comedores(
        {"filters": "[]"}, user=SimpleNamespace(is_superuser=False, pk=7)
    )

    assert out == "filtrado-dupla"
    assert any(call[0] == "manager_filter" for call in dupla_qs.calls)
    assert any(call[0] == "values" for call in dupla_qs.calls)
    filter_mock.assert_called_once_with(dupla_qs, {"filters": "[]"})


def test_get_nomina_detail_calcula_resumen_y_porcentajes(mocker):
    resumen = {
        "cantidad_nomina_m": 3,
        "cantidad_nomina_f": 4,
        "cantidad_nomina_x": 1,
        "espera": 2,
        "cantidad_total": 10,
        "rango_ninos": 2,
        "rango_adolescentes": 1,
        "rango_adultos": 3,
        "rango_adultos_mayores": 2,
        "rango_adulto_mayor_avanzado": 1,
        "rango_total_activos": 9,
    }
    nomina_qs = _NominaQS(resumen)
    mocker.patch(
        "comedores.services.comedor_service.impl.Nomina.objects",
        SimpleNamespace(filter=lambda **_kwargs: nomina_qs),
    )
    page_obj = SimpleNamespace(number=1)
    paginator_mock = mocker.patch(
        "comedores.services.comedor_service.impl.Paginator",
        return_value=SimpleNamespace(get_page=lambda _page: page_obj),
    )

    out = module.ComedorService.get_nomina_detail(99, page=2, per_page=25)

    assert out[0] is page_obj
    assert out[1:6] == (3, 4, 1, 2, 10)
    rangos = out[6]
    assert rangos["total_activos"] == 9
    assert rangos["pct_ninos"] == 22
    assert rangos["pct_adolescentes"] == 11
    assert rangos["pct_adultos"] == 33
    assert rangos["pct_adultos_mayores"] == 22
    assert rangos["pct_adulto_mayor_avanzado"] == 11
    assert any(call[0] == "aggregate" for call in nomina_qs.calls)
    paginator_mock.assert_called_once()


def test_get_comedor_detail_object_prepara_queryset_y_prefetch(mocker):
    class _DetailQS:
        def __init__(self):
            self.select_related_args = None
            self.prefetch_args = None

        def select_related(self, *args):
            self.select_related_args = args
            return self

        def prefetch_related(self, *args):
            self.prefetch_args = args
            return self

    detail_qs = _DetailQS()
    mocker.patch("comedores.services.comedor_service.impl.preload_valores_comida_cache")
    mocker.patch(
        "comedores.services.comedor_service.impl.Comedor.objects",
        SimpleNamespace(select_related=lambda *args: detail_qs.select_related(*args)),
    )
    get_obj_mock = mocker.patch(
        "comedores.services.comedor_service.impl.get_object_or_404",
        return_value="comedor-detalle",
    )

    out = module.ComedorService.get_comedor_detail_object(123)

    assert out == "comedor-detalle"
    assert detail_qs.select_related_args is not None
    assert detail_qs.prefetch_args is not None
    assert len(detail_qs.prefetch_args) >= 6
    prefetch_to_attrs = [
        getattr(arg, "to_attr", None)
        for arg in detail_qs.prefetch_args
        if hasattr(arg, "to_attr")
    ]
    assert "imagenes_optimized" in prefetch_to_attrs
    assert "relevamientos_optimized" in prefetch_to_attrs
    assert "observaciones_optimized" in prefetch_to_attrs
    get_obj_mock.assert_called_once_with(detail_qs, pk=123)
