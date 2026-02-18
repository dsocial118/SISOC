"""Tests for conftest."""

import django.urls
import factory
import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import Client
from faker import Faker

from comedores.models import Comedor
from comedores.tasks import AsyncSendComedorToGestionar

fake = Faker()


class ComedorFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Comedor

    nombre = factory.LazyAttribute(lambda _: fake.company())


@pytest.fixture
def client_logged_fixture(db):
    user_model = get_user_model()
    user_instance = user_model.objects.create_user(
        username=fake.user_name(), password="testpass"
    )
    for group_name in [
        "Comedores Ver",
        "Comedores Relevamiento Ver",
        "Comedores Relevamiento Crear",
        "Comedores Relevamiento Detalle",
        "Comedores Relevamiento Editar",
    ]:
        group, _ = Group.objects.get_or_create(name=group_name)
        user_instance.groups.add(group)
    user_instance.save()

    client = Client()
    client.login(username=user_instance.username, password="testpass")
    return client


@pytest.fixture(autouse=True)
def comedor_fixture(monkeypatch, db):
    comedor = ComedorFactory()
    monkeypatch.setattr(
        "comedores.services.comedor_service.ComedorService.get_comedor_detail_object",
        lambda pk: comedor,
    )
    monkeypatch.setattr(
        "comedores.services.comedor_service.ComedorService.get_presupuestos",
        lambda pk: (10, 1, 2, 3, 4, 5),
    )
    monkeypatch.setattr(
        "rendicioncuentasmensual.services.RendicionCuentaMensualService.cantidad_rendiciones_cuentas_mensuales",
        lambda obj: 5,
    )
    monkeypatch.setattr(comedor.relevamiento_set, "order_by", lambda *a, **kw: [])
    monkeypatch.setattr(comedor.relevamiento_set, "count", lambda: 1)
    monkeypatch.setattr(comedor.observacion_set, "order_by", lambda *a, **kw: [])
    monkeypatch.setattr(comedor.imagenes, "values", lambda *a, **kw: [])
    monkeypatch.setattr(
        comedor.clasificacioncomedor_set.order_by(), "first", lambda: None
    )
    monkeypatch.setattr(comedor.admision_set, "first", lambda: None)
    monkeypatch.setattr(
        "comedores.tasks.AsyncSendComedorToGestionar.start", lambda self: None
    )
    return comedor


@pytest.fixture
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

    # Reemplazar el método run para que no haga nadaGrac
    def mock_run(self):
        pass

    monkeypatch.setattr(AsyncSendComedorToGestionar, "run", mock_run)

    # También podemos mockear el método start para asegurarnos de que no se inicie ningún hilo
    def mock_start(self):
        pass

    monkeypatch.setattr(AsyncSendComedorToGestionar, "start", mock_start)


@pytest.fixture(autouse=True)
def mock_djdt_reverse(monkeypatch):
    original_reverse = django.urls.reverse

    def fake_reverse(viewname, *args, **kwargs):
        if isinstance(viewname, str) and viewname.startswith("djdt:"):
            return "/djdt-mock-url/"
        return original_reverse(viewname, *args, **kwargs)

    monkeypatch.setattr(django.urls, "reverse", fake_reverse)
