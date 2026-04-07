from pathlib import Path

import pytest


MOJIBAKE_MARKERS = ("Ã", "Â", "â", "�")
FILES_WITH_ASCII_SAFE_TEXT = (
    Path("docker/django/entrypoint.py"),
    Path("users/services_auth.py"),
)


@pytest.mark.parametrize("path", FILES_WITH_ASCII_SAFE_TEXT, ids=str)
def test_task_source_files_do_not_contain_mojibake_markers(path):
    content = path.read_text(encoding="utf-8")

    for marker in MOJIBAKE_MARKERS:
        assert (
            marker not in content
        ), f"{path} contiene la secuencia mojibake {marker!r}"
