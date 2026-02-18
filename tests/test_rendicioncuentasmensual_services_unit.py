"""Tests for test rendicioncuentasmensual services unit."""

from types import SimpleNamespace

import pytest

from rendicioncuentasmensual.services import RendicionCuentaMensualService


def test_crear_rendicion_cuenta_mensual_success(mocker):
    comedor = SimpleNamespace(pk=10)
    payload = {
        "mes": 1,
        "anio": 2026,
        "documento_adjunto": "doc.pdf",
        "observaciones": "obs",
        "arvhios_adjuntos": ["a"],
    }
    created = object()
    mock_create = mocker.patch(
        "rendicioncuentasmensual.services.RendicionCuentaMensual.objects.create",
        return_value=created,
    )

    result = RendicionCuentaMensualService.crear_rendicion_cuenta_mensual(
        comedor, payload
    )

    assert result is created
    mock_create.assert_called_once_with(
        comedor=comedor,
        mes=1,
        anio=2026,
        documento_adjunto="doc.pdf",
        observaciones="obs",
        arvhios_adjuntos=["a"],
    )


def test_crear_rendicion_cuenta_mensual_logs_and_raises(mocker):
    comedor = SimpleNamespace(pk=99)
    mocker.patch(
        "rendicioncuentasmensual.services.RendicionCuentaMensual.objects.create",
        side_effect=RuntimeError("db"),
    )
    mock_exc = mocker.patch("rendicioncuentasmensual.services.logger.exception")

    with pytest.raises(RuntimeError):
        RendicionCuentaMensualService.crear_rendicion_cuenta_mensual(comedor, {})

    mock_exc.assert_called_once()


def test_actualizar_rendicion_cuenta_mensual_success():
    rendicion = SimpleNamespace(
        mes=None,
        anio=None,
        documento_adjunto=None,
        observaciones=None,
        arvhios_adjuntos=None,
        save=lambda: None,
    )
    payload = {
        "mes": 2,
        "anio": 2025,
        "documento_adjunto": "b.pdf",
        "observaciones": "ok",
        "arvhios_adjuntos": ["x"],
    }

    result = RendicionCuentaMensualService.actualizar_rendicion_cuenta_mensual(
        rendicion, payload
    )

    assert result is rendicion
    assert rendicion.mes == 2
    assert rendicion.anio == 2025
    assert rendicion.documento_adjunto == "b.pdf"
    assert rendicion.observaciones == "ok"
    assert rendicion.arvhios_adjuntos == ["x"]


def test_actualizar_rendicion_cuenta_mensual_logs_and_raises(mocker):
    payload = {"mes": 2}
    rendicion = SimpleNamespace(
        pk=5, save=mocker.Mock(side_effect=RuntimeError("boom"))
    )
    mock_exc = mocker.patch("rendicioncuentasmensual.services.logger.exception")

    with pytest.raises(RuntimeError):
        RendicionCuentaMensualService.actualizar_rendicion_cuenta_mensual(
            rendicion, payload
        )

    mock_exc.assert_called_once()


def test_eliminar_rendicion_cuenta_mensual_success():
    deleted = {"ok": False}

    def _delete():
        deleted["ok"] = True

    rendicion = SimpleNamespace(delete=_delete)

    RendicionCuentaMensualService.eliminar_rendicion_cuenta_mensual(rendicion)

    assert deleted["ok"] is True


def test_eliminar_rendicion_cuenta_mensual_logs_and_raises(mocker):
    rendicion = SimpleNamespace(pk=3, delete=mocker.Mock(side_effect=RuntimeError("x")))
    mock_exc = mocker.patch("rendicioncuentasmensual.services.logger.exception")

    with pytest.raises(RuntimeError):
        RendicionCuentaMensualService.eliminar_rendicion_cuenta_mensual(rendicion)

    mock_exc.assert_called_once()


def test_obtener_rendiciones_cuentas_mensuales_success(mocker):
    comedor = object()
    prefetch_result = object()
    mock_filter = mocker.patch(
        "rendicioncuentasmensual.services.RendicionCuentaMensual.objects.filter"
    )
    mock_filter.return_value.prefetch_related.return_value = prefetch_result

    result = RendicionCuentaMensualService.obtener_rendiciones_cuentas_mensuales(
        comedor
    )

    assert result is prefetch_result
    mock_filter.assert_called_once_with(comedor=comedor)
    mock_filter.return_value.prefetch_related.assert_called_once_with(
        "arvhios_adjuntos"
    )


def test_obtener_rendiciones_cuentas_mensuales_logs_and_raises(mocker):
    comedor = SimpleNamespace(pk=8)
    mocker.patch(
        "rendicioncuentasmensual.services.RendicionCuentaMensual.objects.filter",
        side_effect=RuntimeError("db"),
    )
    mock_exc = mocker.patch("rendicioncuentasmensual.services.logger.exception")

    with pytest.raises(RuntimeError):
        RendicionCuentaMensualService.obtener_rendiciones_cuentas_mensuales(comedor)

    mock_exc.assert_called_once()


def test_obtener_rendicion_cuenta_mensual_success(mocker):
    expected = object()
    mock_get = mocker.patch(
        "rendicioncuentasmensual.services.get_object_or_404", return_value=expected
    )

    result = RendicionCuentaMensualService.obtener_rendicion_cuenta_mensual(12)

    assert result is expected
    mock_get.assert_called_once()


def test_obtener_rendicion_cuenta_mensual_logs_and_raises(mocker):
    mocker.patch(
        "rendicioncuentasmensual.services.get_object_or_404",
        side_effect=RuntimeError("404"),
    )
    mock_exc = mocker.patch("rendicioncuentasmensual.services.logger.exception")

    with pytest.raises(RuntimeError):
        RendicionCuentaMensualService.obtener_rendicion_cuenta_mensual(77)

    mock_exc.assert_called_once()


def test_cantidad_rendiciones_cuentas_mensuales_success(mocker):
    comedor = object()
    mock_filter = mocker.patch(
        "rendicioncuentasmensual.services.RendicionCuentaMensual.objects.filter"
    )
    mock_filter.return_value.count.return_value = 5

    assert (
        RendicionCuentaMensualService.cantidad_rendiciones_cuentas_mensuales(comedor)
        == 5
    )
    mock_filter.assert_called_once_with(comedor=comedor)
    mock_filter.return_value.count.assert_called_once_with()


def test_cantidad_rendiciones_cuentas_mensuales_logs_and_raises(mocker):
    comedor = SimpleNamespace(pk=2)
    mocker.patch(
        "rendicioncuentasmensual.services.RendicionCuentaMensual.objects.filter",
        side_effect=RuntimeError("err"),
    )
    mock_exc = mocker.patch("rendicioncuentasmensual.services.logger.exception")

    with pytest.raises(RuntimeError):
        RendicionCuentaMensualService.cantidad_rendiciones_cuentas_mensuales(comedor)

    mock_exc.assert_called_once()
