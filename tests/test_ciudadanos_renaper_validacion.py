from datetime import date, datetime, timezone
from unittest.mock import patch

import pytest

from ciudadanos.models import Ciudadano
from ciudadanos.services_importacion_masiva import _build_ciudadano_payload_from_renaper
from ciudadanos.services_renaper_validacion import (
    build_validacion_renaper_payload,
    identidad_coincide,
)


@pytest.mark.parametrize(
    "result,expected_data",
    [
        ({"datos_api": {"crudo": True}, "data": {"mapeado": True}}, {"crudo": True}),
        ({"datos_api": {}, "data": {"mapeado": True}}, {"mapeado": True}),
        ({}, {}),
    ],
)
def test_payload_conserva_contrato_de_importacion(result, expected_data):
    now = datetime(2026, 9, 15, tzinfo=timezone.utc)
    with patch("ciudadanos.services_renaper_validacion.timezone.now", return_value=now):
        assert build_validacion_renaper_payload(result) == {
            "estado_validacion_renaper": Ciudadano.RENAPER_VALIDADO,
            "fecha_validacion_renaper": now,
            "datos_renaper": expected_data,
            "origen_dato": "renaper",
        }


def test_importacion_conserva_payload_completo():
    result = {"data": {"sexo": 1}, "datos_api": {"cuil": "20301112220"}}
    initial = {"nombre": "Ana", "sexo_id": 1, "documento": 30111222}
    now = datetime(2026, 9, 15, tzinfo=timezone.utc)
    with (
        patch(
            "ciudadanos.services_importacion_masiva."
            "construir_datos_ciudadano_desde_renaper",
            return_value=(initial.copy(), None),
        ),
        patch("ciudadanos.services_renaper_validacion.timezone.now", return_value=now),
    ):
        payload, error = _build_ciudadano_payload_from_renaper(
            result=result, dni="30111222", sexo="F"
        )
    assert error is None
    assert payload == {
        **initial,
        "tipo_registro_identidad": Ciudadano.TIPO_REGISTRO_ESTANDAR,
        "estado_validacion_renaper": Ciudadano.RENAPER_VALIDADO,
        "fecha_validacion_renaper": now,
        "datos_renaper": result["datos_api"],
        "origen_dato": "renaper",
        "cuil_cuit": "20301112220",
    }


@pytest.mark.parametrize(
    "fecha", ["2024-01-15", "15/01/2024", "2024/01/15", date(2024, 1, 15)]
)
def test_coincidencia_tolera_representacion_de_fecha_y_nombre(fecha):
    local = {"apellido": "Pérez", "nombre": "Ana María", "fecha_nacimiento": fecha}
    remoto = {
        "apellido": "PÉREZ",
        "nombre": " ANA  MARÍA ",
        "fecha_nacimiento": "15/01/2024",
    }
    assert identidad_coincide(local, remoto)


@pytest.mark.parametrize("campo", ["apellido", "nombre", "fecha_nacimiento"])
def test_identidad_incompleta_nunca_coincide(campo):
    datos = {"apellido": "Pérez", "nombre": "Ana", "fecha_nacimiento": "2024-01-15"}
    datos[campo] = ""
    assert not identidad_coincide(datos, datos)
