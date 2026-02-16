"""Tests unitarios para helpers de acompanamientos.acompanamiento_service."""

from datetime import date, datetime
from types import SimpleNamespace

from acompanamientos.acompanamiento_service import AcompanamientoService


class _QS:
    def __init__(self, first_value=None):
        self._first_value = first_value

    def filter(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def first(self):
        return self._first_value


def test_format_date_variants(mocker):
    assert AcompanamientoService._format_date(None) is None
    assert AcompanamientoService._format_date(date(2024, 1, 2)) == "02/01/2024"

    dt = datetime(2024, 2, 3, 10, 0, 0)
    mocker.patch("acompanamientos.acompanamiento_service.localtime", return_value=dt)
    assert AcompanamientoService._format_date(dt) == "03/02/2024"

    mocker.patch(
        "acompanamientos.acompanamiento_service.localtime",
        side_effect=Exception("tz"),
    )
    assert AcompanamientoService._format_date(dt) == "03/02/2024"

    assert AcompanamientoService._format_date("2024-05-01") == "01/05/2024"
    assert AcompanamientoService._format_date("abc") == "abc"
    assert AcompanamientoService._format_date("2024-12-31XYZ") == "2024-12-31"


def test_obtener_prestaciones_detalladas_none_and_values():
    empty = AcompanamientoService.obtener_prestaciones_detalladas(None)
    assert empty == {
        "prestaciones_por_dia": [],
        "prestaciones_dias": [],
        "dias_semana": [],
    }

    informe = SimpleNamespace(
        aprobadas_desayuno_lunes=1,
        aprobadas_desayuno_martes=2,
        aprobadas_desayuno_miercoles=3,
        aprobadas_desayuno_jueves=4,
        aprobadas_desayuno_viernes=5,
        aprobadas_desayuno_sabado=6,
        aprobadas_desayuno_domingo=7,
        aprobadas_almuerzo_lunes=0,
        aprobadas_almuerzo_martes=0,
        aprobadas_almuerzo_miercoles=0,
        aprobadas_almuerzo_jueves=0,
        aprobadas_almuerzo_viernes=0,
        aprobadas_almuerzo_sabado=0,
        aprobadas_almuerzo_domingo=0,
        aprobadas_merienda_lunes=1,
        aprobadas_merienda_martes=1,
        aprobadas_merienda_miercoles=1,
        aprobadas_merienda_jueves=1,
        aprobadas_merienda_viernes=1,
        aprobadas_merienda_sabado=1,
        aprobadas_merienda_domingo=1,
        aprobadas_cena_lunes=2,
        aprobadas_cena_martes=2,
        aprobadas_cena_miercoles=2,
        aprobadas_cena_jueves=2,
        aprobadas_cena_viernes=2,
        aprobadas_cena_sabado=2,
        aprobadas_cena_domingo=2,
    )

    out = AcompanamientoService.obtener_prestaciones_detalladas(informe)
    assert out["dias_semana"] == [
        "Lunes",
        "Martes",
        "Miercoles",
        "Jueves",
        "Viernes",
        "Sabado",
        "Domingo",
    ]
    assert out["prestaciones_dias"][0] == {"tipo": "Desayuno", "cantidad": 28}
    assert out["prestaciones_dias"][1] == {"tipo": "Almuerzo", "cantidad": 0}


def test_preparar_datos_tabla_comedores_and_permisos():
    admision = SimpleNamespace(
        id=7,
        num_expediente="EX-1",
        estado_admision=True,
        get_estado_admision_display=lambda: "Aprobada",
        modificado=datetime(2024, 1, 1, 0, 0, 0),
    )
    comedor = SimpleNamespace(
        id=1,
        nombre="Comedor A",
        organizacion=SimpleNamespace(nombre="Org"),
        provincia=SimpleNamespace(nombre="BA"),
        dupla="Dupla X",
        admisiones_acompaniamiento=[admision],
    )

    rows = AcompanamientoService.preparar_datos_tabla_comedores([comedor])
    assert rows[0]["cells"][1]["content"] == "Comedor A"
    assert rows[0]["cells"][3]["content"] == "EX-1"
    assert "admision_id=7" in rows[0]["actions"][0]["url"]

    comedor_empty = SimpleNamespace(
        id=2,
        nombre=None,
        organizacion=None,
        provincia=None,
        dupla=None,
        admisiones_acompaniamiento=[],
    )
    rows_empty = AcompanamientoService.preparar_datos_tabla_comedores([comedor_empty])
    assert rows_empty[0]["cells"][1]["content"] == "-"

    user_super = SimpleNamespace(is_superuser=True, groups=SimpleNamespace(filter=lambda **_k: None))
    assert AcompanamientoService.verificar_permisos_tecnico_comedor(user_super) is True

    group_filter = lambda **_kwargs: SimpleNamespace(exists=lambda: True)
    user_group = SimpleNamespace(is_superuser=False, groups=SimpleNamespace(filter=group_filter))
    assert AcompanamientoService.verificar_permisos_tecnico_comedor(user_group) is True


def test_obtener_datos_admision_with_and_without_admision(mocker):
    comedor = SimpleNamespace(pk=1)

    admision = SimpleNamespace(
        id=10,
        comedor_id=5,
        legales_num_if="IF-1",
        numero_disposicion="DISP-1",
    )
    admision_qs = _QS(first_value=admision)

    mocker.patch("acompanamientos.acompanamiento_service.Admision.objects.filter", return_value=admision_qs)
    mocker.patch(
        "acompanamientos.acompanamiento_service.InformeTecnico.objects.filter",
        return_value=_QS(first_value="info"),
    )
    mocker.patch(
        "acompanamientos.acompanamiento_service.Comedor.objects.filter",
        return_value=_QS(first_value="comedor-db"),
    )

    out = AcompanamientoService.obtener_datos_admision(comedor)
    assert out["admision"] is admision
    assert out["comedor"] == "comedor-db"
    assert out["info_relevante"] == "info"
    assert out["numero_if"] == "IF-1"

    mocker.patch("acompanamientos.acompanamiento_service.Admision.objects.filter", return_value=_QS(first_value=None))
    out_none = AcompanamientoService.obtener_datos_admision(comedor)
    assert out_none["admision"] is None
    assert out_none["numero_if"] is None
