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
        "archivos_adjuntos": ["a"],
    }
    created = object()
    mock_create = mocker.patch(
        "rendicioncuentasmensual.services.RendicionCuentaMensual.objects.create",
        return_value=created,
    )
    mock_set_archivos = mocker.patch.object(
        RendicionCuentaMensualService, "_asignar_archivos_adjuntos"
    )

    result = RendicionCuentaMensualService.crear_rendicion_cuenta_mensual(
        comedor, payload
    )

    assert result is created
    mock_create.assert_called_once_with(
        comedor=comedor,
        mes=1,
        anio=2026,
        convenio=None,
        numero_rendicion=None,
        periodo_inicio=None,
        periodo_fin=None,
        estado="elaboracion",
        documento_adjunto="doc.pdf",
        observaciones="obs",
    )
    mock_set_archivos.assert_called_once_with(created, ["a"])


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
        archivos_adjuntos=None,
        save=lambda: None,
    )
    payload = {
        "mes": 2,
        "anio": 2025,
        "documento_adjunto": "b.pdf",
        "observaciones": "ok",
        "archivos_adjuntos": ["x"],
    }
    result = RendicionCuentaMensualService.actualizar_rendicion_cuenta_mensual(
        rendicion, payload
    )

    assert result is rendicion
    assert rendicion.mes == 2
    assert rendicion.anio == 2025
    assert rendicion.documento_adjunto == "b.pdf"
    assert rendicion.observaciones == "ok"
    assert rendicion.archivos_adjuntos == ["x"]


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
    queryset = object()
    project_qs_mock = mocker.patch.object(
        RendicionCuentaMensualService,
        "_get_project_queryset",
        return_value=queryset,
    )

    result = RendicionCuentaMensualService.obtener_rendiciones_cuentas_mensuales(
        comedor
    )

    assert result is queryset
    project_qs_mock.assert_called_once_with(comedor)


def test_get_archivos_adjuntos_data_acepta_key_legacy_y_nueva():
    assert RendicionCuentaMensualService._get_archivos_adjuntos_data(
        {"archivos_adjuntos": ["nuevo"], "arvhios_adjuntos": ["legacy"]}
    ) == ["nuevo"]
    assert RendicionCuentaMensualService._get_archivos_adjuntos_data(
        {"arvhios_adjuntos": ["legacy"]}
    ) == ["legacy"]


def test_asignar_archivos_adjuntos_usa_manager_set_si_existe(mocker):
    manager = mocker.Mock()
    rendicion = SimpleNamespace(archivos_adjuntos=manager)

    RendicionCuentaMensualService._asignar_archivos_adjuntos(rendicion, ["a"])

    manager.set.assert_called_once_with(["a"])


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
    project_qs = mocker.Mock()
    project_qs.count.return_value = 5
    project_qs_mock = mocker.patch.object(
        RendicionCuentaMensualService,
        "_get_project_queryset",
        return_value=project_qs,
    )

    assert (
        RendicionCuentaMensualService.cantidad_rendiciones_cuentas_mensuales(comedor)
        == 5
    )
    project_qs_mock.assert_called_once_with(comedor)
    project_qs.count.assert_called_once_with()


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


def test_obtener_scope_proyecto_con_codigo_y_organizacion(mocker):
    organizacion = SimpleNamespace(nombre="Organizacion A")
    comedor = SimpleNamespace(
        organizacion=organizacion,
        organizacion_id=5,
        codigo_de_proyecto="PROY-01",
        nombre="Comedor Base",
    )
    rendicion = SimpleNamespace(comedor=comedor)
    expected = [SimpleNamespace(nombre="Comedor 1"), SimpleNamespace(nombre="Comedor 2")]
    filter_mock = mocker.patch(
        "rendicioncuentasmensual.services.Comedor.objects.filter",
        return_value=SimpleNamespace(order_by=lambda *_args: expected),
    )

    result = RendicionCuentaMensualService.obtener_scope_proyecto(rendicion)

    assert result["organizacion"] is organizacion
    assert result["proyecto_codigo"] == "PROY-01"
    assert result["comedores_relacionados"] == expected
    filter_mock.assert_called_once_with(
        codigo_de_proyecto="PROY-01",
        deleted_at__isnull=True,
        organizacion_id=5,
    )


def test_obtener_scope_proyecto_sin_codigo_retorna_comedor_actual():
    comedor = SimpleNamespace(
        organizacion=None,
        organizacion_id=None,
        codigo_de_proyecto="",
        nombre="Comedor Unico",
    )
    rendicion = SimpleNamespace(comedor=comedor)

    result = RendicionCuentaMensualService.obtener_scope_proyecto(rendicion)

    assert result["organizacion"] is None
    assert result["proyecto_codigo"] == ""
    assert result["comedores_relacionados"] == [comedor]
