from django.apps import apps


def test_encuestas_app_esta_instalada():
    assert apps.is_installed("encuestas")


def test_encuestas_app_config():
    config = apps.get_app_config("encuestas")
    assert config.verbose_name == "Encuestas"
