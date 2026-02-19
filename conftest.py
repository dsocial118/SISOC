"""Tests for conftest."""

import pytest


@pytest.fixture(autouse=True)
def global_temp_media_root(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path / "media"
