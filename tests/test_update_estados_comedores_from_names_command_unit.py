from argparse import ArgumentParser
from io import StringIO

import pytest
from django.core.management.base import CommandError

from comedores.management.commands import update_estados_comedores_from_names as module


class _DummyStyle:
    @staticmethod
    def SUCCESS(msg):
        return msg

    @staticmethod
    def WARNING(msg):
        return msg

    @staticmethod
    def ERROR(msg):
        return msg


def _command():
    cmd = module.Command()
    cmd.stdout = StringIO()
    cmd.stderr = StringIO()
    cmd.style = _DummyStyle()
    cmd._actividad_cache = {}
    cmd._proceso_cache = {}
    cmd._detalle_cache = {}
    return cmd


def test_add_arguments_registers_expected_options():
    cmd = _command()
    parser = ArgumentParser()
    cmd.add_arguments(parser)
    options = {a.dest for a in parser._actions}
    assert {"csv_path", "delimiter", "encoding", "dry_run"}.issubset(options)


def test_normalize_validate_and_parse_int():
    cmd = _command()
    assert cmd._normalize_header(" Estado General ") == "estado_actividad"
    assert cmd._normalize_header("Subestado") == "estado_proceso"

    with pytest.raises(CommandError):
        cmd._validate_headers({"comedor_id"})
    cmd._validate_headers({"comedor_id", "estado_actividad", "estado_proceso"})

    assert cmd._parse_int_field("10", "x", 2, True) == 10
    assert cmd._parse_int_field("10.9", "x", 2, True) == 10
    with pytest.raises(ValueError):
        cmd._parse_int_field("", "x", 2, True)
    with pytest.raises(ValueError):
        cmd._parse_int_field("abc", "x", 2, True)


def test_iter_rows_validates_headers_and_skips_blank_rows(tmp_path):
    cmd = _command()
    path = tmp_path / "in.csv"
    path.write_text("id,estado,subestado\n1,Activo,En ejecución\n,,\n", encoding="utf-8")

    rows = list(cmd._iter_rows(path, ",", "utf-8"))
    assert rows == [
        (2, {"comedor_id": "1", "estado_actividad": "Activo", "estado_proceso": "En ejecución"})
    ]


def test_resolve_comedor_success_and_missing(mocker):
    cmd = _command()
    comedor = type("C", (), {"pk": 1, "id": 1, "nombre": "Uno"})()
    mocker.patch(
        "comedores.management.commands.update_estados_comedores_from_names.Comedor.objects.get",
        return_value=comedor,
    )
    assert cmd._resolve_comedor({"comedor_id": "1"}, 2, []) is comedor

    missing = []
    does_not_exist = type("ComedorDoesNotExist", (Exception,), {})
    mocker.patch(
        "comedores.management.commands.update_estados_comedores_from_names.Comedor.DoesNotExist",
        does_not_exist,
    )
    mocker.patch(
        "comedores.management.commands.update_estados_comedores_from_names.Comedor.objects.get",
        side_effect=does_not_exist(),
    )
    with pytest.raises(ValueError):
        cmd._resolve_comedor({"comedor_id": "9"}, 3, missing)
    assert missing[-1]["comedor_id"] == 9


def test_resolve_estado_actividad_caches_and_errors(mocker):
    cmd = _command()

    qs = mocker.Mock()
    actividad = type("A", (), {"id": 5, "estado": "Activo"})()
    qs.count.return_value = 1
    qs.first.return_value = actividad
    mock_filter = mocker.patch(
        "comedores.management.commands.update_estados_comedores_from_names.EstadoActividad.objects.filter",
        return_value=qs,
    )

    result1 = cmd._resolve_estado_actividad({"estado_actividad": "Activo"}, 2)
    result2 = cmd._resolve_estado_actividad({"estado_actividad": "Activo"}, 2)
    assert result1 is actividad
    assert result2 is actividad
    mock_filter.assert_called_once()

    qs.count.return_value = 0
    with pytest.raises(ValueError):
        cmd._resolve_estado_actividad({"estado_actividad": "No"}, 3)

    qs.count.return_value = 2
    with pytest.raises(ValueError):
        cmd._resolve_estado_actividad({"estado_actividad": "Dup"}, 4)


def test_resolve_estado_proceso_caches_and_errors(mocker):
    cmd = _command()
    actividad = type("A", (), {"id": 1, "estado": "Activo"})()
    proceso = type("P", (), {"id": 7, "estado": "En ejecución"})()

    base_qs = mocker.Mock()
    base_qs.count.return_value = 1
    base_qs.first.return_value = proceso

    mock_base = mocker.patch(
        "comedores.management.commands.update_estados_comedores_from_names.EstadoProceso.objects.filter",
        return_value=base_qs,
    )

    p1 = cmd._resolve_estado_proceso({"estado_proceso": "En ejecución"}, 2, actividad)
    p2 = cmd._resolve_estado_proceso({"estado_proceso": "En ejecución"}, 2, actividad)
    assert p1 is proceso
    assert p2 is proceso
    mock_base.assert_called_once()

    # count==0 and exists elsewhere
    cmd._proceso_cache.clear()
    base_qs.count.return_value = 0
    mocker.patch(
        "comedores.management.commands.update_estados_comedores_from_names.EstadoProceso.objects.filter",
        side_effect=[base_qs, mocker.Mock(exists=mocker.Mock(return_value=True))],
    )
    with pytest.raises(ValueError):
        cmd._resolve_estado_proceso({"estado_proceso": "Otro"}, 3, actividad)

    # count>1
    cmd._proceso_cache.clear()
    base_qs2 = mocker.Mock()
    base_qs2.count.return_value = 2
    mocker.patch(
        "comedores.management.commands.update_estados_comedores_from_names.EstadoProceso.objects.filter",
        return_value=base_qs2,
    )
    with pytest.raises(ValueError):
        cmd._resolve_estado_proceso({"estado_proceso": "Dup"}, 4, actividad)


def test_resolve_estado_detalle_optional_caches_and_errors(mocker):
    cmd = _command()
    actividad = type("A", (), {"id": 1, "estado": "Activo"})()
    proceso = type("P", (), {"id": 2, "estado": "En ejecución"})()
    detalle = type("D", (), {"id": 3, "estado": "Motivo"})()

    assert cmd._resolve_estado_detalle({"estado_detalle": ""}, 2, proceso, actividad) is None

    base_qs = mocker.Mock()
    base_qs.count.return_value = 1
    base_qs.first.return_value = detalle
    mock_filter = mocker.patch(
        "comedores.management.commands.update_estados_comedores_from_names.EstadoDetalle.objects.filter",
        return_value=base_qs,
    )

    d1 = cmd._resolve_estado_detalle({"estado_detalle": "Motivo"}, 2, proceso, actividad)
    d2 = cmd._resolve_estado_detalle({"estado_detalle": "Motivo"}, 2, proceso, actividad)
    assert d1 is detalle
    assert d2 is detalle
    mock_filter.assert_called_once()

    cmd._detalle_cache.clear()
    base_qs.count.return_value = 0
    mocker.patch(
        "comedores.management.commands.update_estados_comedores_from_names.EstadoDetalle.objects.filter",
        side_effect=[base_qs, mocker.Mock(exists=mocker.Mock(return_value=True))],
    )
    with pytest.raises(ValueError):
        cmd._resolve_estado_detalle({"estado_detalle": "Otro"}, 3, proceso, actividad)


def test_handle_raises_for_missing_file(tmp_path):
    cmd = _command()
    with pytest.raises(CommandError):
        cmd.handle(csv_path=str(tmp_path / "none.csv"), delimiter=",", encoding="utf-8", dry_run=True)


def test_handle_dry_run_and_apply_paths(mocker, tmp_path):
    cmd = _command()
    csv_file = tmp_path / "in.csv"
    csv_file.write_text("id,estado,subestado\n1,Activo,En ejecución\n", encoding="utf-8")

    comedor = type("C", (), {"pk": 1, "id": 1, "nombre": "Uno", "ultimo_estado": type("H", (), {"id": 10})()})()
    actividad = type("A", (), {"estado": "Activo"})()
    proceso = type("P", (), {"estado": "En ejecución"})()

    mocker.patch.object(cmd, "_iter_rows", return_value=[(2, {"a": 1}), (3, {"a": 2})])
    mocker.patch.object(cmd, "_resolve_comedor", side_effect=[ValueError("Línea 2: bad"), comedor])
    mocker.patch.object(cmd, "_resolve_estado_actividad", return_value=actividad)
    mocker.patch.object(cmd, "_resolve_estado_proceso", return_value=proceso)
    mocker.patch.object(cmd, "_resolve_estado_detalle", return_value=None)
    change = mocker.patch(
        "comedores.management.commands.update_estados_comedores_from_names.registrar_cambio_estado",
        return_value=type("H", (), {"id": 10})(),
    )
    atomic = mocker.patch("comedores.management.commands.update_estados_comedores_from_names.transaction.atomic")
    atomic.return_value.__enter__.return_value = None
    atomic.return_value.__exit__.return_value = False

    cmd.handle(csv_path=str(csv_file), delimiter=",", encoding="utf-8", dry_run=True)
    out = cmd.stdout.getvalue()
    assert "[DRY-RUN]" in out
    assert "Filas con errores: 1" in out
    change.assert_not_called()

    cmd2 = _command()
    mocker.patch.object(cmd2, "_iter_rows", return_value=[(2, {"a": 2})])
    mocker.patch.object(cmd2, "_resolve_comedor", return_value=comedor)
    mocker.patch.object(cmd2, "_resolve_estado_actividad", return_value=actividad)
    mocker.patch.object(cmd2, "_resolve_estado_proceso", return_value=proceso)
    mocker.patch.object(cmd2, "_resolve_estado_detalle", return_value=None)

    cmd2.handle(csv_path=str(csv_file), delimiter=",", encoding="utf-8", dry_run=False)
    assert "Filas sin cambios: 1" in cmd2.stdout.getvalue()


def test_print_summary_sections():
    cmd = _command()
    cmd._print_summary(
        stats={"rows": 2, "applied": 1, "skipped": 0, "errors": 1},
        missing_comedores=[{"linea": 2, "comedor_id": 7}],
        error_details=["boom"],
        dry_run=True,
    )
    out = cmd.stdout.getvalue()
    assert "=== Resumen ===" in out
    assert "Comedores no encontrados" in out
    assert "Detalle de errores" in out
    assert "Modo dry-run" in out
