from argparse import ArgumentParser
from io import StringIO
from pathlib import Path

import pytest
from django.core.management.base import CommandError

from comedores.management.commands.update_comedores_dupla import Command


def _command():
    cmd = Command()
    cmd.stdout = StringIO()
    cmd.stderr = StringIO()
    return cmd


def test_add_arguments_registers_expected_options():
    cmd = _command()
    parser = ArgumentParser()
    cmd.add_arguments(parser)
    options = {a.dest for a in parser._actions}
    assert {"csv_path", "dry_run", "admision"}.issubset(options)


def test_parse_int_valid_and_invalid_cases():
    cmd = _command()
    assert cmd._parse_int("10", "dupla_id", 2) == 10
    assert cmd._parse_int("10.0", "dupla_id", 2) == 10

    with pytest.raises(ValueError):
        cmd._parse_int("", "dupla_id", 2)
    with pytest.raises(ValueError):
        cmd._parse_int("abc", "dupla_id", 2)


def test_iter_rows_validates_headers_and_skips_blank_lines(tmp_path):
    cmd = _command()
    empty = tmp_path / "empty.csv"
    empty.write_text("", encoding="utf-8")
    with pytest.raises(CommandError):
        list(cmd._iter_rows(empty))

    good = tmp_path / "good.csv"
    good.write_text(
        "dupla_id,comedor_id\n1,2\n,\n3,4\n",
        encoding="utf-8",
    )
    rows = list(cmd._iter_rows(good))
    assert rows == [
        (2, {"dupla_id": "1", "comedor_id": "2"}),
        (4, {"dupla_id": "3", "comedor_id": "4"}),
    ]

    bad = tmp_path / "bad.csv"
    bad.write_text("dupla_id\n1\n", encoding="utf-8")
    with pytest.raises(CommandError):
        list(cmd._iter_rows(bad))


def test_handle_raises_for_missing_or_invalid_file(tmp_path):
    cmd = _command()
    with pytest.raises(CommandError):
        cmd.handle(csv_path=str(tmp_path / "no.csv"), dry_run=True, admision=False)

    folder = tmp_path / "folder"
    folder.mkdir()
    with pytest.raises(CommandError):
        cmd.handle(csv_path=str(folder), dry_run=True, admision=False)


def test_handle_dry_run_covers_errors_skip_and_detected_updates(mocker, tmp_path):
    cmd = _command()
    csv_file = tmp_path / "in.csv"
    csv_file.write_text("dupla_id,comedor_id\n1,1\n", encoding="utf-8")

    mocker.patch.object(
        cmd,
        "_iter_rows",
        return_value=[
            (2, {"dupla_id": "x", "comedor_id": "1"}),  # parse error
            (3, {"dupla_id": "2", "comedor_id": "99"}),  # comedor missing
            (4, {"dupla_id": "88", "comedor_id": "1"}),  # dupla missing
            (5, {"dupla_id": "5", "comedor_id": "2"}),  # skipped same dupla
            (6, {"dupla_id": "6", "comedor_id": "3"}),  # dry-run update
        ],
    )

    comedor_does_not_exist = type("ComedorDoesNotExist", (Exception,), {})
    dupla_does_not_exist = type("DuplaDoesNotExist", (Exception,), {})
    mocker.patch(
        "comedores.management.commands.update_comedores_dupla.Comedor.DoesNotExist",
        comedor_does_not_exist,
    )
    mocker.patch(
        "comedores.management.commands.update_comedores_dupla.Dupla.DoesNotExist",
        dupla_does_not_exist,
    )

    comedores = {
        1: type("C", (), {"id": 1, "nombre": "C1", "dupla_id": 2})(),
        2: type("C", (), {"id": 2, "nombre": "C2", "dupla_id": 5})(),
        3: type("C", (), {"id": 3, "nombre": "C3", "dupla_id": 1})(),
    }
    duplas = {5: type("D", (), {"id": 5})(), 6: type("D", (), {"id": 6})()}

    def _get_comedor(pk):
        if pk == 99:
            raise comedor_does_not_exist()
        return comedores[pk]

    def _get_dupla(pk):
        if pk == 88:
            raise dupla_does_not_exist()
        return duplas[pk]

    mocker.patch(
        "comedores.management.commands.update_comedores_dupla.Comedor.objects.select_related"
    ).return_value.get.side_effect = _get_comedor
    mocker.patch(
        "comedores.management.commands.update_comedores_dupla.Dupla.objects.get",
        side_effect=_get_dupla,
    )

    cmd.handle(csv_path=str(csv_file), dry_run=True, admision=False)

    out = cmd.stdout.getvalue()
    assert "[DRY-RUN]" in out
    assert "Línea 5" in out
    assert "Filas con errores: 3" in out
    assert "Modo dry-run: no se aplicaron cambios." in out


def test_handle_applies_update_and_creates_related_records(mocker, tmp_path):
    cmd = _command()
    csv_file = tmp_path / "in.csv"
    csv_file.write_text("dupla_id,comedor_id\n1,1\n", encoding="utf-8")
    mocker.patch.object(cmd, "_iter_rows", return_value=[(2, {"dupla_id": "7", "comedor_id": "10"})])

    comedor = type("C", (), {"id": 10, "nombre": "C10", "dupla_id": None, "dupla": None, "estado": None})()
    comedor.save = mocker.Mock()
    dupla = type("D", (), {"id": 7})()
    mocker.patch(
        "comedores.management.commands.update_comedores_dupla.Comedor.objects.select_related"
    ).return_value.get.return_value = comedor
    mocker.patch(
        "comedores.management.commands.update_comedores_dupla.Dupla.objects.get",
        return_value=dupla,
    )
    mocker.patch(
        "comedores.management.commands.update_comedores_dupla.Admision.objects.filter"
    ).return_value.exists.return_value = False
    mock_create_admision = mocker.patch(
        "comedores.management.commands.update_comedores_dupla.Admision.objects.create"
    )
    mocker.patch(
        "comedores.management.commands.update_comedores_dupla.Hitos.objects.filter"
    ).return_value.exists.return_value = False
    mock_create_hitos = mocker.patch(
        "comedores.management.commands.update_comedores_dupla.Hitos.objects.create"
    )
    atomic = mocker.patch("comedores.management.commands.update_comedores_dupla.transaction.atomic")
    atomic.return_value.__enter__.return_value = None
    atomic.return_value.__exit__.return_value = False

    cmd.handle(csv_path=str(csv_file), dry_run=False, admision=True)

    comedor.save.assert_called_once_with(update_fields=["dupla"])
    mock_create_admision.assert_called_once()
    mock_create_hitos.assert_called_once_with(comedor=comedor)
    assert "[APLICADO]" in cmd.stdout.getvalue()
