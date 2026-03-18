from unittest.mock import MagicMock, patch

from pwa.signals import seed_catalogo_actividades


def test_seed_catalogo_actividades_omite_bootstrap_si_tabla_no_existe():
    fake_connection = MagicMock()
    fake_connection.introspection.table_names.return_value = []

    with patch("pwa.signals.connections", {"default": fake_connection}):
        with patch("pwa.signals.bootstrap_catalogo_actividades") as bootstrap_mock:
            seed_catalogo_actividades(sender=None, using="default")

    bootstrap_mock.assert_not_called()


def test_seed_catalogo_actividades_ejecuta_bootstrap_si_tabla_existe():
    fake_connection = MagicMock()
    fake_connection.introspection.table_names.return_value = [
        "pwa_catalogoactividadpwa"
    ]

    with patch("pwa.signals.connections", {"analytics": fake_connection}):
        with patch("pwa.signals.bootstrap_catalogo_actividades") as bootstrap_mock:
            seed_catalogo_actividades(sender=None, using="analytics")

    bootstrap_mock.assert_called_once_with(using="analytics")
