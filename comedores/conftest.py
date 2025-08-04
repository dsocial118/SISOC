import pytest
from django.contrib.auth.models import User
from django.test import Client
import factory
from faker import Faker

from .models import Comedor
from .tasks import AsyncSendComedorToGestionar


fake = Faker()


class ComedorFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Comedor

    nombre = factory.LazyAttribute(lambda _: fake.company())


@pytest.fixture
def client_logged_fixture(db):
    """
    Crea un usuario y un cliente autenticado.
    """
    user = User.objects.create_user(username="testuser", password="password")
    client = Client()
    client.force_login(user)
    return client


@pytest.fixture
def comedor_fixture(db):
    """
    Crea un comedor para usar en los tests.
    """
    return ComedorFactory()


@pytest.fixture(autouse=True)
def mock_async_tasks(monkeypatch):
    """
    Mockea la tarea AsyncSendComedorToGestionar para evitar errores en hilos.
    """
    # Reemplazar el método __init__ para evitar que se guarde el ID del comedor
    original_init = AsyncSendComedorToGestionar.__init__

    def mock_init(self, comedor_id, *args, **kwargs):
        # Llamar al __init__ original pero ignorar los errores relacionados con el ID del comedor
        original_init(self, comedor_id, *args, **kwargs)

    monkeypatch.setattr(AsyncSendComedorToGestionar, "__init__", mock_init)

    # Reemplazar el método run para que no haga nada
    def mock_run(self):
        pass

    monkeypatch.setattr(AsyncSendComedorToGestionar, "run", mock_run)

    # También podemos mockear el método start para asegurarnos de que no se inicie ningún hilo
    def mock_start(self):
        pass

    monkeypatch.setattr(AsyncSendComedorToGestionar, "start", mock_start)
