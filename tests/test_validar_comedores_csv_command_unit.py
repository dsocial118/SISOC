from argparse import ArgumentParser
from io import StringIO

import pytest
from django.core.management.base import CommandError

from comedores.management.commands import validar_comedores_csv as module


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


def test_add_arguments_and_header_helpers():
    cmd = _command()
    parser = ArgumentParser()
    cmd.add_arguments(parser)
    options = {a.dest for a in parser._actions}
    assert {"csv_path", "delimiter", "encoding", "dry_run"}.issubset(options)

    assert cmd._normalize_header(" Comedor ") == "comedor_id"

    with pytest.raises(CommandError):
        cmd._validate_headers(set())
    cmd._validate_headers({"comedor_id"})


def test_parse_int_field_and_normalize_text():
    cmd = _command()

    assert cmd._parse_int_field("10", "x", 2, True) == 10
    assert cmd._parse_int_field("10.0", "x", 2, True) == 10
    with pytest.raises(ValueError):
        cmd._parse_int_field("", "x", 2, True)
    with pytest.raises(ValueError):
        cmd._parse_int_field("10.5", "x", 2, True)
    with pytest.raises(ValueError):
        cmd._parse_int_field("abc", "x", 2, True)

    assert cmd._normalize_text("Ejecución") == "ejecucion"


def test_iter_rows_happy_path_and_header_validation(tmp_path):
    cmd = _command()

    bad = tmp_path / "bad.csv"
    bad.write_text("otra\n1\n", encoding="utf-8")
    with pytest.raises(CommandError):
        list(cmd._iter_rows(bad, ",", "utf-8"))

    good = tmp_path / "good.csv"
    good.write_text("id\n1\n\n", encoding="utf-8")
    assert list(cmd._iter_rows(good, ",", "utf-8")) == [(2, {"comedor_id": "1"})]


def test_resolve_estado_actividad_and_proceso_create_or_fail(mocker):
    cmd = _command()

    qs = mocker.Mock()
    actividad = type("A", (), {"id": 1, "estado": "Activo"})()
    qs.count.return_value = 1
    qs.first.return_value = actividad
    mocker.patch(
        "comedores.management.commands.validar_comedores_csv.EstadoActividad.objects.filter",
        return_value=qs,
    )
    assert cmd._resolve_estado_actividad("Activo", create_missing=False) is actividad

    qs.count.return_value = 0
    with pytest.raises(CommandError):
        cmd._resolve_estado_actividad("Activo", create_missing=False)

    created = type("A", (), {"id": 2, "estado": "Activo"})()
    mocker.patch(
        "comedores.management.commands.validar_comedores_csv.EstadoActividad.objects.create",
        return_value=created,
    )
    assert cmd._resolve_estado_actividad("Activo", create_missing=True) is created

    qs.count.return_value = 2
    with pytest.raises(CommandError):
        cmd._resolve_estado_actividad("Activo", create_missing=True)


def test_resolve_estado_proceso_variants(mocker):
    cmd = _command()
    actividad = type("A", (), {"id": 1, "estado": "Activo"})()

    qs = mocker.Mock()
    proceso = type("P", (), {"id": 3, "estado": "En ejecución"})()
    qs.count.return_value = 1
    qs.first.return_value = proceso
    mocker.patch(
        "comedores.management.commands.validar_comedores_csv.EstadoProceso.objects.filter",
        return_value=qs,
    )
    assert cmd._resolve_estado_proceso(actividad, "En ejecución", create_missing=False) is proceso

    qs.count.return_value = 2
    with pytest.raises(CommandError):
        cmd._resolve_estado_proceso(actividad, "En ejecución", create_missing=True)

    qs.count.return_value = 0
    # fallback normalize equivalence
    cand1 = type("P", (), {"estado": "EN EJECUCION"})()
    mocker.patch(
        "comedores.management.commands.validar_comedores_csv.EstadoProceso.objects.filter",
        side_effect=[qs, [cand1]],
    )
    assert cmd._resolve_estado_proceso(actividad, "En ejecución", create_missing=False) is cand1

    # create when missing and allowed
    mocker.patch(
        "comedores.management.commands.validar_comedores_csv.EstadoProceso.objects.filter",
        side_effect=[qs, []],
    )
    created = type("P", (), {"id": 9})()
    mocker.patch(
        "comedores.management.commands.validar_comedores_csv.EstadoProceso.objects.create",
        return_value=created,
    )
    assert cmd._resolve_estado_proceso(actividad, "En ejecución", create_missing=True) is created

    mocker.patch(
        "comedores.management.commands.validar_comedores_csv.EstadoProceso.objects.filter",
        side_effect=[qs, []],
    )
    with pytest.raises(CommandError):
        cmd._resolve_estado_proceso(actividad, "En ejecución", create_missing=False)


def test_matches_estado_actual_and_update_stats():
    cmd = _command()
    actividad = type("A", (), {"id": 1})()
    proceso = type("P", (), {"id": 2})()

    comedor = type("C", (), {"ultimo_estado": None})()
    assert cmd._matches_estado_actual(comedor, actividad, proceso) is False

    estado_general_ok = type(
        "EG", (), {"estado_actividad_id": 1, "estado_proceso_id": 2, "estado_detalle_id": None}
    )()
    comedor_ok = type("C", (), {"ultimo_estado": type("U", (), {"estado_general_id": 5, "estado_general": estado_general_ok})()})()
    assert cmd._matches_estado_actual(comedor_ok, actividad, proceso) is True

    stats = {
        "applied": 0,
        "skipped": 0,
        "validacion_updates": 0,
        "validacion_skipped": 0,
        "estado_updates": 0,
        "estado_skipped": 0,
    }
    cmd._update_stats(stats, validacion_changed=True, estado_changed=False, applied=True)
    cmd._update_stats(stats, validacion_changed=False, estado_changed=False, applied=False)
    assert stats["applied"] == 1
    assert stats["skipped"] == 1
    assert stats["validacion_updates"] == 1
    assert stats["estado_skipped"] == 2


def test_handle_raises_for_missing_or_invalid_file(tmp_path):
    cmd = _command()
    with pytest.raises(CommandError):
        cmd.handle(csv_path=str(tmp_path / "none.csv"), delimiter=",", encoding="utf-8", dry_run=True)

    folder = tmp_path / "f"
    folder.mkdir()
    with pytest.raises(CommandError):
        cmd.handle(csv_path=str(folder), delimiter=",", encoding="utf-8", dry_run=True)


def test_handle_dry_run_and_apply_paths(mocker, tmp_path):
    csv_file = tmp_path / "in.csv"
    csv_file.write_text("id\n1\n", encoding="utf-8")

    # dry-run path
    cmd = _command()
    actividad = type("A", (), {"id": 1, "estado": "Activo"})()
    proceso = type("P", (), {"id": 2, "estado": "En ejecución"})()
    comedor = type("C", (), {
        "id": 1,
        "pk": 1,
        "nombre": "Uno",
        "estado_validacion": "Pendiente",
        "fecha_validado": None,
        "ultimo_estado": None,
    })()

    mocker.patch.object(cmd, "_resolve_estado_actividad", return_value=actividad)
    mocker.patch.object(cmd, "_resolve_estado_proceso", return_value=proceso)
    mocker.patch.object(cmd, "_iter_rows", return_value=[(2, {"comedor_id": "x"}), (3, {"comedor_id": "1"})])
    mocker.patch(
        "comedores.management.commands.validar_comedores_csv.Comedor.objects.select_related"
    ).return_value.get.return_value = comedor

    cmd.handle(csv_path=str(csv_file), delimiter=",", encoding="utf-8", dry_run=True)
    out = cmd.stdout.getvalue()
    assert "[DRY-RUN]" in out
    assert "Filas con errores: 1" in out
    assert "Modo dry-run" in out

    # apply path with and without cambios
    cmd2 = _command()
    comedor2 = type("C", (), {
        "id": 2,
        "pk": 2,
        "nombre": "Dos",
        "estado_validacion": module.VALIDACION_ESTADO,
        "fecha_validado": object(),
        "ultimo_estado": type("U", (), {"id": 10, "estado_general_id": 4, "estado_general": type("EG", (), {"estado_actividad_id": 1, "estado_proceso_id": 2, "estado_detalle_id": None})()})(),
    })()
    comedor2.save = mocker.Mock()

    mocker.patch.object(cmd2, "_resolve_estado_actividad", return_value=actividad)
    mocker.patch.object(cmd2, "_resolve_estado_proceso", return_value=proceso)
    mocker.patch.object(cmd2, "_iter_rows", return_value=[(2, {"comedor_id": "2"})])
    mocker.patch(
        "comedores.management.commands.validar_comedores_csv.Comedor.objects.select_related"
    ).return_value.get.return_value = comedor2
    mocker.patch(
        "comedores.management.commands.validar_comedores_csv.registrar_cambio_estado",
        return_value=type("H", (), {"id": 10})(),
    )
    mocker.patch("comedores.management.commands.validar_comedores_csv.HistorialValidacion.objects.create")
    atomic = mocker.patch("comedores.management.commands.validar_comedores_csv.transaction.atomic")
    atomic.return_value.__enter__.return_value = None
    atomic.return_value.__exit__.return_value = False

    cmd2.handle(csv_path=str(csv_file), delimiter=",", encoding="utf-8", dry_run=False)
    assert "(sin cambios)" in cmd2.stdout.getvalue()


def test_print_summary_sections():
    cmd = _command()
    cmd._print_summary(
        stats={
            "rows": 2,
            "applied": 1,
            "validacion_updates": 1,
            "estado_updates": 0,
            "skipped": 0,
            "errors": 1,
        },
        missing_comedores=[{"linea": 2, "comedor_id": 8}],
        error_details=["boom"],
        dry_run=True,
    )
    out = cmd.stdout.getvalue()
    assert "=== Resumen ===" in out
    assert "Comedores no encontrados" in out
    assert "Detalle de errores" in out
    assert "Modo dry-run" in out
