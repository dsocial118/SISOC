"""Tests for conftest."""

from unittest import mock

import factory
import pytest
from django.contrib.auth.models import Group
from django.utils import timezone
from faker import Faker
import django.urls

from comedores.models import Comedor
from relevamientos.models import Relevamiento

# Configurar Faker para obtener resultados consistentes
fake = Faker()
fake.seed_instance(12345)


class ComedorFactory(factory.django.DjangoModelFactory):
    """Factory para crear instancias de Comedor para tests."""

    class Meta:
        model = Comedor

    nombre = factory.LazyAttribute(lambda _: fake.company())


class RelevamientoFactory(factory.django.DjangoModelFactory):
    """Factory para crear instancias de Relevamiento para tests."""

    class Meta:
        model = Relevamiento

    comedor = factory.SubFactory(ComedorFactory)
    fecha_visita = factory.LazyFunction(timezone.now)


@pytest.fixture
def client_logged(db, django_user_model, client):
    # Crear usuario con permisos directamente aquí
    user_instance = django_user_model.objects.create_user(
        username=fake.user_name(), password="testpass"
    )

    for group_name in [
        "Comedores Relevamiento Ver",
        "Comedores Relevamiento Crear",
        "Comedores Relevamiento Detalle",
        "Comedores Relevamiento Editar",
        "Comedores Ver",
    ]:
        group_obj, _ = Group.objects.get_or_create(name=group_name)
        user_instance.groups.add(group_obj)
    user_instance.save()

    # Login
    client.login(username=user_instance.username, password="testpass")
    return client


@pytest.fixture(name="comedor")
def comedor_fixture(db):
    return ComedorFactory()


@pytest.fixture
def relevamiento(comedor):
    # Crear relevamiento con ese comedor
    rel_instance = RelevamientoFactory(comedor=comedor)
    rel_instance.responsable = mock.Mock()
    rel_instance.responsable.nombre = fake.first_name()
    rel_instance.responsable.apellido = fake.last_name()
    rel_instance.responsable.mail = fake.email()
    rel_instance.responsable.celular = fake.phone_number()
    rel_instance.responsable.documento = fake.ssn()
    return rel_instance


@pytest.fixture(autouse=True)
def mock_async_tasks(monkeypatch):
    monkeypatch.setattr(
        "relevamientos.tasks.AsyncSendRelevamientoToGestionar.start", lambda self: None
    )
    monkeypatch.setattr(
        "relevamientos.tasks.AsyncRemoveRelevamientoToGestionar.start",
        lambda self: None,
    )
    monkeypatch.setattr(
        "comedores.tasks.AsyncSendComedorToGestionar.start", lambda self: None
    )
    monkeypatch.setattr(
        "comedores.tasks.AsyncRemoveComedorToGestionar.start", lambda self: None
    )
    monkeypatch.setattr(
        "comedores.tasks.AsyncSendReferenteToGestionar.start", lambda self: None
    )
    monkeypatch.setattr(
        "comedores.tasks.AsyncSendObservacionToGestionar.start", lambda self: None
    )


@pytest.fixture(autouse=True)
def mock_djdt_reverse(monkeypatch):
    original_reverse = django.urls.reverse

    def fake_reverse(viewname, *args, **kwargs):
        if isinstance(viewname, str) and viewname.startswith("djdt:"):
            return "/djdt-mock-url/"
        return original_reverse(viewname, *args, **kwargs)

    monkeypatch.setattr(django.urls, "reverse", fake_reverse)
