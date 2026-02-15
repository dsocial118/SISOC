from argparse import ArgumentParser
from io import StringIO

import pytest
from django.core.management.base import CommandError

from comedores.management.commands import update_estados_comedores as module


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
    return cmd


def test_add_arguments_registers_expected_options():
    cmd = _command()
    parser = ArgumentParser()

    cmd.add_arguments(parser)

    options = {a.dest for a in parser._actions}
    assert {"csv_path", "delimiter", "dry_run"}.issubset(options)


def test_normalize_validate_headers_and_parse_int():
    cmd = _command()

    assert cmd._normalize_header(" comedor__nombre ") == "nombre"
    assert cmd._normalize_header("ESTADOPROCESO") == "estado_proceso"

    with pytest.raises(CommandError):
        cmd._validate_headers({"estado_actividad"})
    with pytest.raises(CommandError):
        cmd._validate_headers({"sisoc_id"})

    cmd._validate_headers({"sisoc_id", "estado_actividad"})

    assert cmd._parse_int_field(None, "x", 3) is None
    assert cmd._parse_int_field("10", "x", 3) == 10
    assert cmd._parse_int_field("10.7", "x", 3) == 10
    with pytest.raises(ValueError):
        cmd._parse_int_field("", "x", 3, required=True)
    with pytest.raises(ValueError):
        cmd._parse_int_field("abc", "x", 3)


def test_iter_rows_validates_headers_and_skips_blank_rows(tmp_path):
    cmd = _command()

    empty = tmp_path / "empty.csv"
    empty.write_text("", encoding="utf-8")
    with pytest.raises(CommandError):
        list(cmd._iter_rows(empty, ","))

    bad = tmp_path / "bad.csv"
    bad.write_text("otra\n1\n", encoding="utf-8")
    with pytest.raises(CommandError):
        list(cmd._iter_rows(bad, ","))

    good = tmp_path / "good.csv"
    good.write_text(
        "id,estadoactividad,estadoproceso\n1,2,3\n,,\n\n",
        encoding="utf-8",
    )
    rows = list(cmd._iter_rows(good, ","))
    assert rows == [(2, {"sisoc_id": "1", "estado_actividad": "2", "estado_proceso": "3"})]


def test_resolve_comedor_by_id_and_name_paths(mocker):
    cmd = _command()
    missing = []

    comedor = type("C", (), {"pk": 5, "id": 5, "nombre": "A"})()
    mocker.patch(
        "comedores.management.commands.update_estados_comedores.Comedor.objects.get",
        return_value=comedor,
    )
    assert cmd._resolve_comedor({"sisoc_id": "5"}, 2, missing) is comedor

    does_not_exist = type("ComedorDoesNotExist", (Exception,), {})
    mocker.patch(
        "comedores.management.commands.update_estados_comedores.Comedor.DoesNotExist",
        does_not_exist,
    )
    mocker.patch(
        "comedores.management.commands.update_estados_comedores.Comedor.objects.get",
        side_effect=does_not_exist(),
    )
    with pytest.raises(ValueError):
        cmd._resolve_comedor({"sisoc_id": "9", "nombre": "X"}, 3, missing)
    assert missing[-1]["sisoc_id"] == 9

    qs = mocker.Mock()
    qs.count.return_value = 1
    qs.first.return_value = comedor
    mocker.patch(
        "comedores.management.commands.update_estados_comedores.Comedor.objects.filter",
        return_value=qs,
    )
    assert cmd._resolve_comedor({"nombre": "A"}, 4, missing) is comedor

    qs.count.return_value = 0
    with pytest.raises(ValueError):
        cmd._resolve_comedor({"nombre": "No"}, 5, missing)

    qs.count.return_value = 2
    with pytest.raises(ValueError):
        cmd._resolve_comedor({"nombre": "Dup"}, 6, missing)

    with pytest.raises(ValueError):
        cmd._resolve_comedor({}, 7, missing)


def test_resolve_estados_success_and_error_paths(mocker):
    cmd = _command()

    actividad = type("A", (), {"id": 1})()
    proceso = type("P", (), {"id": 2, "estado_actividad_id": 1})()
    detalle = type("D", (), {"id": 3, "estado_proceso_id": 2, "estado_proceso": proceso})()

    mocker.patch(
        "comedores.management.commands.update_estados_comedores.EstadoActividad.objects.get",
        return_value=actividad,
    )
    mocker.patch(
        "comedores.management.commands.update_estados_comedores.EstadoProceso.objects.get",
        return_value=proceso,
    )
    mocker.patch(
        "comedores.management.commands.update_estados_comedores.EstadoDetalle.objects.get",
        return_value=detalle,
    )

    assert cmd._resolve_estados(
        {"estado_actividad": "1", "estado_proceso": "2", "estado_detalle": "3"}, 2
    ) == (actividad, proceso, detalle)

    bad_proceso = type("P", (), {"id": 2, "estado_actividad_id": 9})()
    mocker.patch(
        "comedores.management.commands.update_estados_comedores.EstadoProceso.objects.get",
        return_value=bad_proceso,
    )
    with pytest.raises(ValueError):
        cmd._resolve_estados({"estado_actividad": "1", "estado_proceso": "2"}, 3)

    mocker.patch(
        "comedores.management.commands.update_estados_comedores.EstadoProceso.objects.get",
        return_value=proceso,
    )
    bad_detalle = type("D", (), {"id": 3, "estado_proceso_id": 8, "estado_proceso": proceso})()
    mocker.patch(
        "comedores.management.commands.update_estados_comedores.EstadoDetalle.objects.get",
        return_value=bad_detalle,
    )
    with pytest.raises(ValueError):
        cmd._resolve_estados(
            {"estado_actividad": "1", "estado_proceso": "2", "estado_detalle": "3"},
            4,
        )

    bad_detalle2 = type("D", (), {"id": 3, "estado_proceso_id": 2, "estado_proceso": type("P", (), {"id": 2, "estado_actividad_id": 9})()})()
    mocker.patch(
        "comedores.management.commands.update_estados_comedores.EstadoDetalle.objects.get",
        return_value=bad_detalle2,
    )
    with pytest.raises(ValueError):
        cmd._resolve_estados({"estado_actividad": "1", "estado_detalle": "3"}, 5)


def test_resolve_estados_does_not_exist_branches(mocker):
    cmd = _command()

    missing_activity = type("MissingA", (Exception,), {})
    mocker.patch(
        "comedores.management.commands.update_estados_comedores.EstadoActividad.DoesNotExist",
        missing_activity,
    )
    mocker.patch(
        "comedores.management.commands.update_estados_comedores.EstadoActividad.objects.get",
        side_effect=missing_activity(),
    )
    with pytest.raises(ValueError):
        cmd._resolve_estados({"estado_actividad": "1"}, 2)

    actividad = type("A", (), {"id": 1})()
    missing_process = type("MissingP", (Exception,), {})
    mocker.patch(
        "comedores.management.commands.update_estados_comedores.EstadoActividad.objects.get",
        return_value=actividad,
    )
    mocker.patch(
        "comedores.management.commands.update_estados_comedores.EstadoProceso.DoesNotExist",
        missing_process,
    )
    mocker.patch(
        "comedores.management.commands.update_estados_comedores.EstadoProceso.objects.get",
        side_effect=missing_process(),
    )
    with pytest.raises(ValueError):
        cmd._resolve_estados({"estado_actividad": "1", "estado_proceso": "2"}, 3)

    proceso = type("P", (), {"id": 2, "estado_actividad_id": 1})()
    missing_detail = type("MissingD", (Exception,), {})
    mocker.patch(
        "comedores.management.commands.update_estados_comedores.EstadoProceso.objects.get",
        return_value=proceso,
    )
    mocker.patch(
        "comedores.management.commands.update_estados_comedores.EstadoDetalle.DoesNotExist",
        missing_detail,
    )
    mocker.patch(
        "comedores.management.commands.update_estados_comedores.EstadoDetalle.objects.get",
        side_effect=missing_detail(),
    )
    with pytest.raises(ValueError):
        cmd._resolve_estados(
            {"estado_actividad": "1", "estado_proceso": "2", "estado_detalle": "3"},
            4,
        )


def test_handle_raises_for_missing_or_invalid_file(tmp_path):
    cmd = _command()

    with pytest.raises(CommandError):
        cmd.handle(csv_path=str(tmp_path / "no.csv"), delimiter=",", dry_run=False)

    folder = tmp_path / "folder"
    folder.mkdir()
    with pytest.raises(CommandError):
        cmd.handle(csv_path=str(folder), delimiter=",", dry_run=False)


def test_handle_dry_run_and_error_collection(mocker, tmp_path):
    cmd = _command()
    csv_file = tmp_path / "in.csv"
    csv_file.write_text("id,estado_actividad\n1,1\n", encoding="utf-8")

    mocker.patch.object(
        cmd,
        "_iter_rows",
        return_value=[
            (2, {"sisoc_id": "x"}),
            (3, {"sisoc_id": "1", "estado_actividad": "1"}),
        ],
    )
    mocker.patch.object(
        cmd,
        "_resolve_comedor",
        side_effect=[ValueError("Línea 2: bad"), type("C", (), {"pk": 1, "id": 1, "nombre": "Uno"})()],
    )
    mocker.patch.object(
        cmd,
        "_resolve_estados",
        return_value=(type("A", (), {"id": 1})(), None, None),
    )
    mock_change = mocker.patch(
        "comedores.management.commands.update_estados_comedores.registrar_cambio_estado"
    )

    cmd.handle(csv_path=str(csv_file), delimiter=",", dry_run=True)

    out = cmd.stdout.getvalue()
    assert "[DRY-RUN]" in out
    assert "Filas procesadas: 2" in out
    assert "Filas con errores: 1" in out
    assert "Modo dry-run" in out
    mock_change.assert_not_called()


def test_handle_apply_counts_applied_and_skipped(mocker, tmp_path):
    cmd = _command()
    csv_file = tmp_path / "in.csv"
    csv_file.write_text("id,estado_actividad\n1,1\n", encoding="utf-8")

    comedor1 = type("C", (), {"pk": 1, "id": 1, "nombre": "Uno", "ultimo_estado": type("H", (), {"id": 10})()})()
    comedor2 = type("C", (), {"pk": 2, "id": 2, "nombre": "Dos", "ultimo_estado": type("H", (), {"id": 20})()})()

    mocker.patch.object(
        cmd,
        "_iter_rows",
        return_value=[(2, {"a": 1}), (3, {"a": 2})],
    )
    mocker.patch.object(cmd, "_resolve_comedor", side_effect=[comedor1, comedor2])
    mocker.patch.object(
        cmd,
        "_resolve_estados",
        return_value=(type("A", (), {"id": 1})(), None, None),
    )
    mocker.patch(
        "comedores.management.commands.update_estados_comedores.registrar_cambio_estado",
        side_effect=[type("H", (), {"id": 99})(), type("H", (), {"id": 20})()],
    )

    atomic = mocker.patch("comedores.management.commands.update_estados_comedores.transaction.atomic")
    atomic.return_value.__enter__.return_value = None
    atomic.return_value.__exit__.return_value = False

    cmd.handle(csv_path=str(csv_file), delimiter=",", dry_run=False)

    out = cmd.stdout.getvalue()
    assert "Actualizaciones aplicadas: 1" in out
    assert "Filas sin cambios: 1" in out
    assert "Filas con errores: 0" in out


def test_print_summary_with_missing_and_error_details():
    cmd = _command()
    cmd._print_summary(
        stats={"rows": 3, "applied": 1, "skipped": 1, "errors": 1},
        missing_comedores=[{"linea": 2, "nombre": "X", "sisoc_id": 7}],
        error_details=["boom"],
        dry_run=False,
    )

    out = cmd.stdout.getvalue()
    assert "=== Resumen ===" in out
    assert "Comedores no encontrados" in out
    assert "Detalle de errores" in out


def test_print_summary_dry_run_note():
    cmd = _command()
    cmd._print_summary(
        stats={"rows": 1, "applied": 0, "skipped": 0, "errors": 0},
        missing_comedores=[],
        error_details=[],
        dry_run=True,
    )
    assert "Modo dry-run" in cmd.stdout.getvalue()
