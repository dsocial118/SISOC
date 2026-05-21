import importlib
from unittest.mock import Mock

import pytest


migration_0005 = importlib.import_module(
    "dispositivos.migrations.0005_remove_dispositivo_domicilio_institucion_and_more"
)


def _apps_with_existing_dispositivos(exists):
    manager = Mock()
    manager.exists.return_value = exists
    dispositivo = Mock()
    dispositivo.objects = manager
    apps = Mock()
    apps.get_model.return_value = dispositivo
    return apps


def test_migration_0005_aborta_si_hay_dispositivos_cargados():
    apps = _apps_with_existing_dispositivos(True)

    with pytest.raises(RuntimeError, match="datos legacy de Dispositivo"):
        migration_0005.assert_no_legacy_contact_data(apps, None)


def test_migration_0005_continua_si_no_hay_dispositivos_cargados():
    apps = _apps_with_existing_dispositivos(False)

    migration_0005.assert_no_legacy_contact_data(apps, None)
