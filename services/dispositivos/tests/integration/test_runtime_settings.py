import os
import subprocess
import sys


def test_dispositivos_runtime_loads_its_own_wsgi_and_urls():
    environment = os.environ | {
        "DJANGO_SETTINGS_MODULE": "services.dispositivos.runtime.settings",
        "DJANGO_SECRET_KEY": "test-secret-key",
    }
    check_runtime = """
import django
django.setup()
from django.conf import settings
assert settings.ROOT_URLCONF == 'services.dispositivos.runtime.urls'
assert settings.WSGI_APPLICATION == 'services.dispositivos.runtime.wsgi.application'
assert settings.DISPOSITIVOS_REGISTER_FAVORITES is False
"""

    result = subprocess.run(
        [sys.executable, "-c", check_runtime],
        capture_output=True,
        check=False,
        env=environment,
        text=True,
    )

    assert result.returncode == 0, result.stderr
