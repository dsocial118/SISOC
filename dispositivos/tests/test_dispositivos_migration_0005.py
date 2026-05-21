import importlib
from unittest.mock import Mock


migration_0005 = importlib.import_module(
    "dispositivos.migrations.0005_remove_dispositivo_domicilio_institucion_and_more"
)


class LegacyDispositivo:
    def __init__(self, domicilio, telefono):
        self.domicilio_institucion = domicilio
        self.telefono_contacto = telefono
        self.calle = ""
        self.altura = ""
        self.telefono_prefijo = ""
        self.telefono_numero = ""
        self.saved_update_fields = None

    def save(self, update_fields):
        self.saved_update_fields = update_fields


class LegacyQuerySet:
    def __init__(self, rows):
        self.rows = rows

    def iterator(self, chunk_size):
        return iter(self.rows)


def _apps_with_rows(rows):
    manager = Mock()
    manager.all.return_value = LegacyQuerySet(rows)
    dispositivo = Mock()
    dispositivo.objects = manager
    apps = Mock()
    apps.get_model.return_value = dispositivo
    return apps


def test_migration_0005_backfill_preserva_domicilio_y_telefono_legacy():
    row = LegacyDispositivo("Av. Siempre Viva 742", "(221) 123-4567")
    apps = _apps_with_rows([row])

    migration_0005.backfill_contacto_desdoblado(apps, None)

    assert row.calle == "Av. Siempre Viva"
    assert row.altura == "742"
    assert row.telefono_prefijo == "221"
    assert row.telefono_numero == "1234567"
    assert row.saved_update_fields == [
        "calle",
        "altura",
        "telefono_prefijo",
        "telefono_numero",
    ]


def test_migration_0005_backfill_usa_sin_numero_cuando_no_puede_partir_altura():
    row = LegacyDispositivo("Parador Municipal", "1123456789")
    apps = _apps_with_rows([row])

    migration_0005.backfill_contacto_desdoblado(apps, None)

    assert row.calle == "Parador Municipal"
    assert row.altura == "S/N"
    assert row.telefono_prefijo == "11"
    assert row.telefono_numero == "23456789"


def test_migration_0005_backfill_usa_fallbacks_si_legacy_esta_vacio():
    row = LegacyDispositivo("", "")
    apps = _apps_with_rows([row])

    migration_0005.backfill_contacto_desdoblado(apps, None)

    assert row.calle == "S/D"
    assert row.altura == "S/N"
    assert row.telefono_prefijo == "0"
    assert row.telefono_numero == "0"


def test_migration_0005_backfill_no_sobrescribe_campos_nuevos_existentes():
    row = LegacyDispositivo("Av. Vieja 100", "2211234567")
    row.calle = "Calle Nueva"
    row.altura = "200"
    row.telefono_prefijo = "11"
    row.telefono_numero = "22222222"
    apps = _apps_with_rows([row])

    migration_0005.backfill_contacto_desdoblado(apps, None)

    assert row.calle == "Calle Nueva"
    assert row.altura == "200"
    assert row.telefono_prefijo == "11"
    assert row.telefono_numero == "22222222"
