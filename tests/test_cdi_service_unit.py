import sys
from types import ModuleType, SimpleNamespace

import pytest

from cdi.services.cdi_service import CentroDesarrolloInfantilService


def test_get_centros_filtrados_without_query_returns_values_qs(mocker):
    values_qs = mocker.Mock()
    mock_values = mocker.patch(
        "cdi.services.cdi_service.CentroDesarrolloInfantil.objects.values",
        return_value=values_qs,
    )

    result = CentroDesarrolloInfantilService.get_centros_filtrados()

    assert result is values_qs
    mock_values.assert_called_once_with(
        "id", "nombre", "provincia", "municipio", "localidad", "direccion"
    )
    values_qs.filter.assert_not_called()


def test_get_centros_filtrados_with_query_applies_filter(mocker):
    filtered_qs = object()
    values_qs = mocker.Mock()
    values_qs.filter.return_value = filtered_qs
    mocker.patch(
        "cdi.services.cdi_service.CentroDesarrolloInfantil.objects.values",
        return_value=values_qs,
    )

    result = CentroDesarrolloInfantilService.get_centros_filtrados("abc")

    assert result is filtered_qs
    values_qs.filter.assert_called_once()


def test_get_centros_filtrados_logs_and_raises_on_error(mocker):
    mocker.patch(
        "cdi.services.cdi_service.CentroDesarrolloInfantil.objects.values",
        side_effect=RuntimeError("db"),
    )
    mock_exc = mocker.patch("cdi.services.cdi_service.logger.exception")

    with pytest.raises(RuntimeError):
        CentroDesarrolloInfantilService.get_centros_filtrados("x")

    mock_exc.assert_called_once()


def test_get_centro_detail_object_success(mocker):
    expected = object()
    mock_get = mocker.patch("cdi.services.cdi_service.get_object_or_404", return_value=expected)
    select_related = mocker.patch(
        "cdi.services.cdi_service.CentroDesarrolloInfantil.objects.select_related",
        return_value="qs",
    )

    result = CentroDesarrolloInfantilService.get_centro_detail_object(22)

    assert result is expected
    select_related.assert_called_once_with("provincia", "municipio", "localidad")
    mock_get.assert_called_once_with("qs", pk=22)


def test_get_centro_detail_object_logs_and_raises(mocker):
    mocker.patch(
        "cdi.services.cdi_service.CentroDesarrolloInfantil.objects.select_related",
        side_effect=RuntimeError("db"),
    )
    mock_exc = mocker.patch("cdi.services.cdi_service.logger.exception")

    with pytest.raises(RuntimeError):
        CentroDesarrolloInfantilService.get_centro_detail_object(1)

    mock_exc.assert_called_once()


def test_create_imagenes_success_using_injected_form_module(mocker):
    class DummyForm:
        def __init__(self, data, files):
            self.data = data
            self.files = files

        def is_valid(self):
            return True

        def save(self):
            return "saved"

    fake_module = ModuleType("cdi.services.forms")
    fake_module.ImagenCentroDesarrolloInfantilForm = DummyForm
    mocker.patch.dict(sys.modules, {"cdi.services.forms": fake_module})

    result = CentroDesarrolloInfantilService.create_imagenes("img", 5)

    assert result == "saved"


def test_create_imagenes_returns_errors_when_invalid(mocker):
    class DummyForm:
        def __init__(self, data, files):
            self.errors = {"imagen": ["invalid"]}

        def is_valid(self):
            return False

    fake_module = ModuleType("cdi.services.forms")
    fake_module.ImagenCentroDesarrolloInfantilForm = DummyForm
    mocker.patch.dict(sys.modules, {"cdi.services.forms": fake_module})

    result = CentroDesarrolloInfantilService.create_imagenes("img", 6)

    assert result == {"imagen": ["invalid"]}


def test_create_imagenes_logs_and_raises(mocker):
    mocker.patch.dict(sys.modules, {})
    mock_exc = mocker.patch("cdi.services.cdi_service.logger.exception")

    with pytest.raises(Exception):
        CentroDesarrolloInfantilService.create_imagenes("img", 1)

    mock_exc.assert_called_once()


def test_get_mes_dia_turno_ids_success(mocker):
    meses = object()
    dias = object()
    turnos = object()
    mocker.patch("cdi.services.cdi_service.Mes.objects.filter", return_value=meses)
    mocker.patch("cdi.services.cdi_service.Dia.objects.filter", return_value=dias)
    mocker.patch("cdi.services.cdi_service.Turno.objects.filter", return_value=turnos)
    payload = {
        "meses_funcionamiento": ["Enero"],
        "dias_funcionamiento": ["Lunes"],
        "turnos_funcionamiento": ["Mañana"],
    }

    result = CentroDesarrolloInfantilService.get_mes_dia_turno_ids(payload)

    assert result["meses_funcionamiento"] is meses
    assert result["dias_funcionamiento"] is dias
    assert result["turnos_funcionamiento"] is turnos


def test_get_mes_dia_turno_ids_logs_and_raises(mocker):
    mocker.patch("cdi.services.cdi_service.Mes.objects.filter", side_effect=RuntimeError("x"))
    mock_exc = mocker.patch("cdi.services.cdi_service.logger.exception")

    with pytest.raises(RuntimeError):
        CentroDesarrolloInfantilService.get_mes_dia_turno_ids({"meses_funcionamiento": ["X"]})

    mock_exc.assert_called_once()


def test_get_informacion_adicional_success(mocker):
    centro = SimpleNamespace(
        cantidad_ninos=30,
        cantidad_trabajadores=7,
        horario_inicio="08:00",
        horario_fin="16:00",
    )
    mocker.patch("cdi.services.cdi_service.CentroDesarrolloInfantil.objects.get", return_value=centro)

    result = CentroDesarrolloInfantilService.get_informacion_adicional(9)

    assert result == {
        "total_ninos": 30,
        "total_trabajadores": 7,
        "horario": "08:00 - 16:00",
    }


def test_get_informacion_adicional_logs_and_raises(mocker):
    mocker.patch(
        "cdi.services.cdi_service.CentroDesarrolloInfantil.objects.get",
        side_effect=RuntimeError("db"),
    )
    mock_exc = mocker.patch("cdi.services.cdi_service.logger.exception")

    with pytest.raises(RuntimeError):
        CentroDesarrolloInfantilService.get_informacion_adicional(3)

    mock_exc.assert_called_once()
