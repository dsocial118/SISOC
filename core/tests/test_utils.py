import os
import stat
from datetime import datetime
from unittest.mock import patch

from core.utils import DailyFileHandler


def test_daily_file_handler_creates_group_writable_log_path(tmp_path):
    previous_umask = os.umask(0o022)
    try:
        with patch("core.utils.timezone.localtime", return_value=datetime(2026, 7, 14)):
            handler = DailyFileHandler(tmp_path / "critical.log")
    finally:
        os.umask(previous_umask)

    handler.close()
    daily_folder = tmp_path / "2026-07-14"
    log_file = daily_folder / "critical.log"

    assert stat.S_IMODE(daily_folder.stat().st_mode) & stat.S_IWGRP
    assert stat.S_IMODE(log_file.stat().st_mode) & stat.S_IWGRP
