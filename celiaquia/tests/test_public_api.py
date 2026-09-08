"""Contrato público de Celiaquía."""

from datetime import datetime
from types import SimpleNamespace

from celiaquia.api import LegajoResumenCiudadano, obtener_resumen_ciudadano


class _LegajosQuery:
    def __init__(self, legajos):
        self.legajos = legajos

    def select_related(self, *args):
        assert args == ("expediente__estado", "estado")
        return self

    def order_by(self, *args):
        assert args == ("-creado_en",)
        return self.legajos


def test_obtener_resumen_ciudadano_expone_dtos_y_no_modelos(mocker):
    creado_en = datetime(2026, 8, 7, 10, 30)
    legajo = SimpleNamespace(
        expediente=SimpleNamespace(estado=SimpleNamespace(nombre="EN_PROCESO")),
        estado=SimpleNamespace(nombre="PENDIENTE"),
        get_resultado_sintys_display=lambda: "Sin resultado",
        get_estado_cupo_display=lambda: "No evaluado",
        es_titular_activo=True,
        get_revision_tecnico_display=lambda: "Pendiente",
        creado_en=creado_en,
    )
    filter_mock = mocker.patch(
        "celiaquia.services.ciudadano_resumen_service.impl.ExpedienteCiudadano.objects.filter",
        return_value=_LegajosQuery([legajo]),
    )

    resumen = obtener_resumen_ciudadano(42)

    filter_mock.assert_called_once_with(ciudadano_id=42)
    assert isinstance(resumen.legajo_actual, LegajoResumenCiudadano)
    assert resumen.historial == (resumen.legajo_actual,)
    assert resumen.legajo_actual.estado_expediente == "EN_PROCESO"
    assert resumen.legajo_actual.estado_legajo == "PENDIENTE"
    assert resumen.legajo_actual.resultado_cruce == "Sin resultado"
    assert resumen.legajo_actual.estado_cupo == "No evaluado"
    assert resumen.legajo_actual.es_titular_activo is True
    assert resumen.legajo_actual.revision_tecnica == "Pendiente"
    assert resumen.legajo_actual.creado_en == creado_en


def test_obtener_resumen_ciudadano_sin_legajos(mocker):
    mocker.patch(
        "celiaquia.services.ciudadano_resumen_service.impl.ExpedienteCiudadano.objects.filter",
        return_value=_LegajosQuery([]),
    )

    resumen = obtener_resumen_ciudadano(42)

    assert resumen.legajo_actual is None
    assert resumen.historial == ()
