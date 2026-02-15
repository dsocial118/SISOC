from argparse import ArgumentParser
from io import StringIO

import pytest
from django.core.management.base import CommandError

from comedores.management.commands import import_comedores_excel as module


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

    @staticmethod
    def NOTICE(msg):
        return msg


def _command():
    cmd = module.Command()
    cmd.stdout = StringIO()
    cmd.stderr = StringIO()
    cmd.style = _DummyStyle()
    return cmd


def test_normalize_header_and_clean_cell_helpers():
    assert module.normalize_header("  NOMBRE DEL COMEDOR ") == "nombre_del_comedor"
    assert module.normalize_header("Código/Postal") == "codigo_postal"

    assert module.clean_cell("  hola  ") == "hola"
    assert module.clean_cell("   ") is None
    assert module.clean_cell(float("nan")) is None
    assert module.clean_cell(7.5) == 7.5


def test_parse_int_and_float_and_as_string():
    assert module.parse_int(None, "x") == (None, None)
    assert module.parse_int(9, "x") == (9, None)
    assert module.parse_int("10,8", "x") == (10, None)
    _, err = module.parse_int("abc", "x")
    assert "No se pudo convertir" in err

    assert module.parse_float(None, "x") == (None, None)
    assert module.parse_float(1.5, "x") == (1.5, None)
    assert module.parse_float("7,3", "x") == (7.3, None)
    _, errf = module.parse_float("xyz", "x")
    assert "No se pudo convertir" in errf

    assert module.as_string("  valor ") == "valor"
    assert module.as_string(" ") is None
    assert module.as_string(None) is None


def test_build_header_map_row_has_values_and_register_warnings():
    headers = ["ID", "Nombre del comedor", "Sin mapear", None, "Lat"]
    hmap = module.build_header_map(headers)
    assert hmap == {0: "id_sisoc", 1: "nombre", 4: "latitud"}

    assert module.row_has_values({"a": None, "b": None}) is False
    assert module.row_has_values({"a": None, "b": 1}) is True

    warnings = {"k": []}
    module.register_warnings(warnings, "k", ["w1", "w2"])
    assert warnings["k"] == ["w1", "w2"]


def test_resolve_estado_components_uses_mapping_and_cache(mocker):
    module._estados_cache.clear()

    act_obj = object()
    proc_obj = object()
    det_obj = object()

    get_act = mocker.patch(
        "comedores.management.commands.import_comedores_excel.EstadoActividad.objects.get_or_create",
        return_value=(act_obj, True),
    )
    get_proc = mocker.patch(
        "comedores.management.commands.import_comedores_excel.EstadoProceso.objects.get_or_create",
        return_value=(proc_obj, True),
    )
    get_det = mocker.patch(
        "comedores.management.commands.import_comedores_excel.EstadoDetalle.objects.get_or_create",
        return_value=(det_obj, True),
    )

    # Mapeo custom con detalle para cubrir ese branch.
    original = module.ESTADO_LABEL_MAPPING.get("Activo")
    module.ESTADO_LABEL_MAPPING["Activo"] = {
        "actividad": "Activo",
        "proceso": "En ejecución",
        "detalle": "Detalle X",
    }
    try:
        res1 = module.resolve_estado_components("Activo")
        res2 = module.resolve_estado_components("Activo")
    finally:
        module.ESTADO_LABEL_MAPPING["Activo"] = original

    assert res1 == (act_obj, proc_obj, det_obj)
    assert res2 == res1
    get_act.assert_called_once()
    get_proc.assert_called_once()
    get_det.assert_called_once()


def test_resolve_estado_components_for_empty_and_unknown_label():
    module._estados_cache.clear()

    assert module.resolve_estado_components("") is None
    assert module.resolve_estado_components("no-existe") is None
    assert module._estados_cache["no-existe"] is None


def test_set_estado_general_from_label_only_when_resolved(mocker):
    comedor = object()
    mock_resolve = mocker.patch(
        "comedores.management.commands.import_comedores_excel.resolve_estado_components"
    )
    mock_change = mocker.patch(
        "comedores.management.commands.import_comedores_excel.registrar_cambio_estado"
    )

    mock_resolve.return_value = None
    module.set_estado_general_from_label(comedor, "Activo")
    mock_change.assert_not_called()

    activity, process, detail = object(), object(), object()
    mock_resolve.return_value = (activity, process, detail)
    module.set_estado_general_from_label(comedor, "Activo")
    mock_change.assert_called_once_with(
        comedor=comedor,
        actividad=activity,
        proceso=process,
        detalle=detail,
    )


def test_resolvers_programa_tipo_and_location(mocker):
    programa_qs = mocker.Mock()
    programa_qs.first.return_value = "prog"
    mocker.patch(
        "comedores.management.commands.import_comedores_excel.Programas.objects.filter",
        return_value=programa_qs,
    )
    assert module.resolve_programa("P") == ("prog", None)

    programa_qs.first.return_value = None
    _, warn = module.resolve_programa("P")
    assert "Programa 'P' no encontrado" == warn

    tipo_qs = mocker.Mock()
    tipo_qs.first.return_value = "tipo"
    mocker.patch(
        "comedores.management.commands.import_comedores_excel.TipoDeComedor.objects.filter",
        return_value=tipo_qs,
    )
    assert module.resolve_tipocomedor("T") == ("tipo", None)
    tipo_qs.first.return_value = None
    _, warn = module.resolve_tipocomedor("T")
    assert "Tipo de comedor 'T' no encontrado" == warn

    prov_qs = mocker.Mock()
    prov_qs.first.return_value = "prov"
    mocker.patch(
        "comedores.management.commands.import_comedores_excel.Provincia.objects.filter",
        return_value=prov_qs,
    )
    assert module.resolve_provincia("PR") == ("prov", None)
    prov_qs.first.return_value = None
    _, warn = module.resolve_provincia("PR")
    assert "Provincia 'PR' no encontrada" == warn

    mun_qs = mocker.Mock()
    mun_qs.filter.return_value = mun_qs
    mun_qs.first.return_value = "mun"
    mocker.patch(
        "comedores.management.commands.import_comedores_excel.Municipio.objects.filter",
        return_value=mun_qs,
    )
    assert module.resolve_municipio("M", provincia="prov") == ("mun", None)
    mun_qs.first.return_value = None
    _, warn = module.resolve_municipio("M", provincia=None)
    assert "Municipio 'M' no encontrado" == warn

    loc_qs = mocker.Mock()
    loc_qs.filter.return_value = loc_qs
    loc_qs.first.return_value = "loc"
    mocker.patch(
        "comedores.management.commands.import_comedores_excel.Localidad.objects.filter",
        return_value=loc_qs,
    )
    assert module.resolve_localidad("L", municipio="mun") == ("loc", None)
    loc_qs.first.return_value = None
    _, warn = module.resolve_localidad("L", municipio=None)
    assert "Localidad 'L' no encontrada" == warn


def test_add_arguments_registers_expected_options():
    cmd = _command()
    parser = ArgumentParser()

    cmd.add_arguments(parser)

    options = {a.dest for a in parser._actions}
    assert {"file_path", "sheet_name", "dry_run"}.issubset(options)


def test_load_rows_dispatches_by_extension_and_validates_sheet_name(mocker):
    cmd = _command()
    mock_excel = mocker.patch.object(cmd, "_load_rows_from_excel", return_value=[["h"], [1]])
    mock_csv = mocker.patch.object(cmd, "_load_rows_from_csv", return_value=[["h"], [1]])

    assert cmd._load_rows("a.xlsx", None) == [["h"], [1]]
    mock_excel.assert_called_once_with("a.xlsx", None)

    assert cmd._load_rows("a.csv", None) == [["h"], [1]]
    mock_csv.assert_called_once_with("a.csv")

    with pytest.raises(CommandError):
        cmd._load_rows("a.csv", "Hoja1")

    with pytest.raises(CommandError):
        cmd._load_rows("a.txt", None)


def test_load_rows_from_excel_handles_active_sheet_and_missing_sheet(mocker):
    cmd = _command()

    active_sheet = mocker.Mock()
    active_sheet.iter_rows.return_value = [("h1", "h2"), (1, 2)]
    wb = mocker.Mock()
    wb.sheetnames = ["Main"]
    wb.active = active_sheet
    wb.__getitem__ = mocker.Mock(return_value=active_sheet)

    mocker.patch(
        "comedores.management.commands.import_comedores_excel.load_workbook",
        return_value=wb,
    )

    assert cmd._load_rows_from_excel("file.xlsx", None) == [["h1", "h2"], [1, 2]]

    with pytest.raises(CommandError):
        cmd._load_rows_from_excel("file.xlsx", "Other")


def test_load_rows_from_excel_specific_sheet(mocker):
    cmd = _command()
    sheet = mocker.Mock()
    sheet.iter_rows.return_value = [("h",), ("v",)]
    wb = mocker.Mock()
    wb.sheetnames = ["Main"]
    wb.active = sheet
    wb.__getitem__ = mocker.Mock(return_value=sheet)

    mocker.patch(
        "comedores.management.commands.import_comedores_excel.load_workbook",
        return_value=wb,
    )

    assert cmd._load_rows_from_excel("file.xlsx", "Main") == [["h"], ["v"]]


def test_load_rows_from_csv_handles_sniffer_and_fallback(tmp_path, mocker):
    cmd = _command()
    csv_file = tmp_path / "data.csv"
    csv_file.write_text("a;b\n1;2\n", encoding="utf-8")

    rows = cmd._load_rows_from_csv(str(csv_file))
    assert rows[0] == ["a", "b"]

    mocker.patch(
        "comedores.management.commands.import_comedores_excel.csv.Sniffer.sniff",
        side_effect=module.csv.Error(),
    )
    csv_file2 = tmp_path / "data2.csv"
    csv_file2.write_text("a,b\n1,2\n", encoding="utf-8")

    rows2 = cmd._load_rows_from_csv(str(csv_file2))
    assert rows2 == [["a", "b"], ["1", "2"]]


def test_handle_raises_for_missing_file(mocker):
    cmd = _command()
    mocker.patch("comedores.management.commands.import_comedores_excel.os.path.exists", return_value=False)

    with pytest.raises(CommandError):
        cmd.handle(file_path="/tmp/no.xlsx", sheet_name=None, dry_run=False)


def test_handle_warns_for_empty_file_rows(mocker):
    cmd = _command()
    mocker.patch("comedores.management.commands.import_comedores_excel.os.path.exists", return_value=True)
    mocker.patch.object(cmd, "_load_rows", return_value=[])

    cmd.handle(file_path="/tmp/x.csv", sheet_name=None, dry_run=False)

    assert "no contiene filas" in cmd.stdout.getvalue().lower()


def test_handle_raises_when_no_valid_headers(mocker):
    cmd = _command()
    mocker.patch("comedores.management.commands.import_comedores_excel.os.path.exists", return_value=True)
    mocker.patch.object(cmd, "_load_rows", return_value=[["columna desconocida"], ["v"]])

    with pytest.raises(CommandError):
        cmd.handle(file_path="/tmp/x.csv", sheet_name=None, dry_run=False)


def test_handle_dry_run_update_and_create_paths_with_warnings_and_failures(mocker):
    cmd = _command()
    mocker.patch("comedores.management.commands.import_comedores_excel.os.path.exists", return_value=True)
    mocker.patch.object(
        cmd,
        "_load_rows",
        return_value=[
            ["id", "programa", "nombre", "tipocomedor", "numero", "lat"],
            ["abc", "Prog", None, None, None, None],
            ["10", "Prog", None, None, None, None],
            [None, None, None, None, None, None],
            [None, "X", "Comedor 1", "Tipo X", "a", "b"],
        ],
    )

    does_not_exist = type("ComedorDoesNotExist", (Exception,), {})
    mocker.patch(
        "comedores.management.commands.import_comedores_excel.Comedor.DoesNotExist",
        does_not_exist,
    )

    get_comedor = mocker.patch(
        "comedores.management.commands.import_comedores_excel.Comedor.objects.get",
        side_effect=does_not_exist(),
    )
    mock_save = mocker.patch("comedores.management.commands.import_comedores_excel.Comedor.save")
    mock_state = mocker.patch(
        "comedores.management.commands.import_comedores_excel.set_estado_general_from_label"
    )

    mocker.patch(
        "comedores.management.commands.import_comedores_excel.resolve_programa",
        return_value=(None, "Programa 'X' no encontrado"),
    )
    mocker.patch(
        "comedores.management.commands.import_comedores_excel.resolve_tipocomedor",
        return_value=(None, "Tipo de comedor 'Tipo X' no encontrado"),
    )

    cmd.handle(file_path="/tmp/x.csv", sheet_name=None, dry_run=True)

    out = cmd.stdout.getvalue()
    assert "DRY RUN activo" in out
    assert "Comedores actualizados (0): -" in out
    assert "Comedores creados (1): (simulado) Comedor 1" in out
    assert "No se pudieron procesar" in out
    assert "id_sisoc=abc" in out
    assert "id_sisoc=10" in out
    assert "Programa 'X' no encontrado" in out
    assert "Tipo de comedor 'Tipo X' no encontrado" in out

    get_comedor.assert_called_once_with(pk=10)
    mock_save.assert_not_called()
    mock_state.assert_not_called()


def test_handle_non_dry_run_updates_and_creates(mocker):
    cmd = _command()
    mocker.patch("comedores.management.commands.import_comedores_excel.os.path.exists", return_value=True)
    mocker.patch.object(
        cmd,
        "_load_rows",
        return_value=[
            ["id", "programa", "nombre"],
            ["1", "Prog", None],
            [None, "Prog", "Nuevo"],
        ],
    )

    comedor_existing = type("ComedorObj", (), {"id": 1, "programa": None})()
    comedor_existing.save = mocker.Mock()

    mocker.patch(
        "comedores.management.commands.import_comedores_excel.Comedor.objects.get",
        return_value=comedor_existing,
    )
    created = type("ComedorObj", (), {"id": 77, "nombre": "Nuevo"})()
    mock_create = mocker.patch(
        "comedores.management.commands.import_comedores_excel.Comedor.objects.create",
        return_value=created,
    )
    mocker.patch(
        "comedores.management.commands.import_comedores_excel.resolve_programa",
        return_value=("prog", None),
    )
    mock_state = mocker.patch(
        "comedores.management.commands.import_comedores_excel.set_estado_general_from_label"
    )
    atomic = mocker.patch("comedores.management.commands.import_comedores_excel.transaction.atomic")
    atomic.return_value.__enter__.return_value = None
    atomic.return_value.__exit__.return_value = False

    cmd.handle(file_path="/tmp/x.csv", sheet_name=None, dry_run=False)

    comedor_existing.save.assert_called_once_with(update_fields=["programa"])
    mock_create.assert_called_once()
    assert mock_state.call_count == 2

    out = cmd.stdout.getvalue()
    assert "Comedores actualizados (1): 1" in out
    assert "Comedores creados (1): 77" in out
    assert "Todas las filas reconocidas" in out
