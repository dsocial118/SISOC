from contextlib import nullcontext
from datetime import date, datetime
from types import SimpleNamespace

import pytest

from comedores.services import comedor_service as module

pytestmark = pytest.mark.django_db


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
            out = [x for x in out if getattr(getattr(x, "municipio", None), "provincia", None) == prov]
        return _QS(out)


def test_parse_fecha_and_text_normalizers():
    assert module.ComedorService._parse_fecha_renaper("2024-01-20") == date(2024, 1, 20)
    assert module.ComedorService._parse_fecha_renaper("20/01/2024") == date(2024, 1, 20)
    assert module.ComedorService._parse_fecha_renaper("20240120") == date(2024, 1, 20)
    assert module.ComedorService._parse_fecha_renaper(datetime(2024, 1, 20, 10, 0)) == datetime(2024, 1, 20, 10, 0)
    assert module.ComedorService._parse_fecha_renaper("invalid") is None

    assert module.ComedorService._replace_number_words("uno y dos") == "1 y dos"
    assert module.ComedorService._to_camel_case("  juAN   peREZ ") == "Juan Perez"
    assert module.ComedorService._apply_geo_alias("caba") == "ciudad autonoma de buenos aires"
    assert module.ComedorService._normalize_geo_value("Veintidós - CABA") == "22 caba"
    assert module.ComedorService._normalize_text("Árbol_Grande") == "arbol grande"


def test_match_geo_mapear_and_nacionalidad(mocker):
    prov = SimpleNamespace(pk=1, nombre="Buenos Aires")
    mun = SimpleNamespace(pk=2, nombre="General Pueyrredon", provincia=prov)
    loc = SimpleNamespace(pk=3, nombre="Mar del Plata", municipio=mun)

    mocker.patch("comedores.services.comedor_service.Provincia.objects.all", return_value=_QS([prov]))
    mocker.patch("comedores.services.comedor_service.Municipio.objects.all", return_value=_QS([mun]))
    mocker.patch("comedores.services.comedor_service.Localidad.objects.all", return_value=_QS([loc]))

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
    mocker.patch("comedores.services.comedor_service.Nacionalidad.objects.all", return_value=[nac])
    assert module.ComedorService._match_nacionalidad("argentina") is nac


def test_consultar_renaper_and_build_data(mocker):
    mocker.patch(
        "comedores.services.comedor_service.consultar_datos_renaper",
        side_effect=[
            {"success": False, "error": "x"},
            {"success": True, "data": {"dni": "123"}},
        ],
    )
    ok = module.ComedorService._consultar_renaper_por_dni("123")
    assert ok["success"] is True

    mocker.patch(
        "comedores.services.comedor_service.consultar_datos_renaper",
        side_effect=[
            {"success": False, "error": "x"},
            {"success": False, "error": "y"},
            {"success": False, "error": "z"},
        ],
    )
    fail = module.ComedorService._consultar_renaper_por_dni("123")
    assert fail["success"] is False

    mocker.patch.object(module.ComedorService, "_mapear_ubicacion_desde_renaper", return_value={"provincia": None, "municipio": None, "localidad": None})
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
        "comedores.services.comedor_service.consultar_datos_renaper",
        return_value={"success": False, "error": "no"},
    )
    out = module.ComedorService.obtener_datos_ciudadano_desde_renaper("12345678", sexo="M")
    assert out["success"] is False

    mocker.patch.object(
        module.ComedorService,
        "_consultar_renaper_por_dni",
        return_value={"success": True, "data": {"apellido": "A", "nombre": "B", "fecha_nacimiento": "2020-01-01", "dni": "12345678"}, "datos_api": {"k": 1}},
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
        "comedores.services.comedor_service.Ciudadano.objects.filter",
        return_value=SimpleNamespace(first=lambda: existing),
    )
    ex = module.ComedorService.crear_ciudadano_desde_renaper("12345678")
    assert ex["created"] is False

    mocker.patch(
        "comedores.services.comedor_service.Ciudadano.objects.filter",
        return_value=SimpleNamespace(first=lambda: None),
    )
    mocker.patch.object(
        module.ComedorService,
        "obtener_datos_ciudadano_desde_renaper",
        return_value={"success": True, "data": {"documento": 123}, "datos_api": {}},
    )
    created = SimpleNamespace(pk=2)
    mocker.patch("comedores.services.comedor_service.Ciudadano.objects.create", return_value=created)
    new = module.ComedorService.crear_ciudadano_desde_renaper("12345678", user=SimpleNamespace(is_authenticated=True))
    assert new["created"] is True


def test_agregar_nomina_and_crear_y_agregar(mocker):
    mocker.patch("comedores.services.comedor_service.get_object_or_404", return_value=SimpleNamespace(pk=1))
    mocker.patch(
        "comedores.services.comedor_service.Nomina.objects.filter",
        return_value=SimpleNamespace(exists=lambda: True),
    )
    ok, _msg = module.ComedorService.agregar_ciudadano_a_nomina(1, 1, user="u")
    assert ok is False

    mocker.patch(
        "comedores.services.comedor_service.Nomina.objects.filter",
        return_value=SimpleNamespace(exists=lambda: False),
    )
    mocker.patch("comedores.services.comedor_service.transaction.atomic", return_value=nullcontext())
    mocker.patch("comedores.services.comedor_service.Nomina.objects.create")
    ok2, _msg2 = module.ComedorService.agregar_ciudadano_a_nomina(1, 1, user="u")
    assert ok2 is True

    c = SimpleNamespace(id=9, delete=mocker.Mock())
    mocker.patch("comedores.services.comedor_service.Ciudadano.objects.create", return_value=c)
    mocker.patch.object(module.ComedorService, "agregar_ciudadano_a_nomina", return_value=(False, "x"))
    ok3, _msg3 = module.ComedorService.crear_ciudadano_y_agregar_a_nomina({}, 1, "u", None, None)
    assert ok3 is False
    assert c.delete.called
