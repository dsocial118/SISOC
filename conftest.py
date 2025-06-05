import pytest
from django.core.management import call_command
from io import StringIO


@pytest.fixture(scope="session")
def django_db_setup(django_db_blocker):
    """
    Se ejecuta una vez al iniciar la sesión de tests.
    Carga las fixtures iniciales necesarias desde el comando custom.
    Crea el superusuario por defecto desde el comando custom.
    Crea los grupos necesarios para los permisos desde el comando custom.
    """
    with django_db_blocker.unblock():
        silent = StringIO()
        call_command("load_fixtures", stdout=silent)
        call_command("create_local_superuser", stdout=silent)
        call_command("create_groups", stdout=silent)
