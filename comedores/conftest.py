import factory
import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import Client
from faker import Faker

from comedores.models import Comedor

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
        lambda pk: (10, 1, 2, 3, 4),
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
        "configuraciones.templatetags.custom_filters.has_group",
        lambda user, group: (
            False
            if user is None
            else (
                    hasattr(user, "groups")
                    and (
                            user.groups.filter(name=group).exists()
                            or getattr(user, "is_superuser", False)
                    )
            )
        ),
    )
    monkeypatch.setattr(
        "comedores.tasks.AsyncSendComedorToGestionar.start", lambda self: None
    )
    return comedor
