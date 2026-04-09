import logging
from pathlib import Path

from core.utils import DailyFileHandler


def test_daily_file_handler_uses_primary_path_when_writable(mocker, tmp_path):
    mocker.patch("core.utils._get_current_log_date_folder", return_value="2026-04-09")
    ensure_writable = mocker.patch("core.utils._ensure_log_file_is_writable")
    file_handler_init = mocker.patch.object(
        logging.FileHandler,
        "__init__",
        autospec=True,
        return_value=None,
    )
    primary_filename = tmp_path / "logs" / "critical.log"

    DailyFileHandler(str(primary_filename))

    expected_daily_filename = tmp_path / "logs" / "2026-04-09" / "critical.log"
    ensure_writable.assert_called_once_with(
        expected_daily_filename,
        mode="a",
        encoding=None,
    )
    assert Path(file_handler_init.call_args.args[1]) == expected_daily_filename


def test_daily_file_handler_uses_fallback_when_primary_path_is_not_writable(
    mocker,
    tmp_path,
    monkeypatch,
    capsys,
):
    mocker.patch("core.utils._get_current_log_date_folder", return_value="2026-04-09")
    fallback_dir = tmp_path / "fallback-logs"
    monkeypatch.setenv("LOG_FALLBACK_DIR", str(fallback_dir))
    primary_filename = tmp_path / "restricted" / "critical.log"
    expected_primary_daily_filename = (
        tmp_path / "restricted" / "2026-04-09" / "critical.log"
    )
    expected_fallback_daily_filename = fallback_dir / "2026-04-09" / "critical.log"

    def _ensure_side_effect(path, mode="a", encoding=None):
        if path == expected_primary_daily_filename:
            raise PermissionError("denied")

    ensure_writable = mocker.patch(
        "core.utils._ensure_log_file_is_writable",
        side_effect=_ensure_side_effect,
    )
    file_handler_init = mocker.patch.object(
        logging.FileHandler,
        "__init__",
        autospec=True,
        return_value=None,
    )

    DailyFileHandler(str(primary_filename))

    assert ensure_writable.call_count == 2
    assert ensure_writable.call_args_list[0].args[0] == expected_primary_daily_filename
    assert ensure_writable.call_args_list[1].args[0] == expected_fallback_daily_filename
    assert Path(file_handler_init.call_args.args[1]) == expected_fallback_daily_filename
    assert "Usando fallback" in capsys.readouterr().err
