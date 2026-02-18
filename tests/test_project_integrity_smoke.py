"""Tests for test project integrity smoke."""

import pytest
from django.core.management import call_command

pytestmark = pytest.mark.smoke


def test_collectstatic_dry_run(settings, tmp_path):
    settings.STATIC_ROOT = tmp_path / "static_root"
    settings.STATIC_ROOT.mkdir(parents=True, exist_ok=True)
    call_command("collectstatic", dry_run=True, interactive=False, verbosity=0)
