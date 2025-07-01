import factory
import pytest
from django.urls import reverse
from django.utils import timezone
from faker import Faker
from unittest import mock

from comedores.models import Comedor
from relevamientos.models import Relevamiento

fake = Faker()


class ComedorFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Comedor

    nombre = factory.LazyAttribute(lambda _: fake.company())


class RelevamientoFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Relevamiento

    comedor = factory.SubFactory(ComedorFactory)
    fecha_visita = factory.LazyFunction(timezone.now)


@pytest.fixture
def user(db, django_user_model):
    user = django_user_model.objects.create_user(
        username=fake.user_name(), password="testpass"
    )
    from django.contrib.auth.models import Group

    for group_name in [
        "Comedores Relevamiento Ver",
        "Comedores Relevamiento Crear",
        "Comedores Relevamiento Detalle",
        "Comedores Relevamiento Editar",
        "Comedores Ver",
    ]:
        group, _ = Group.objects.get_or_create(name=group_name)
        user.groups.add(group)
    user.save()
    return user


@pytest.fixture
def client_logged(user, client):
    client.login(username=user.username, password="testpass")
    return client


@pytest.fixture
def comedor():
    return ComedorFactory()


@pytest.fixture
def relevamiento(comedor):
    relevamiento = RelevamientoFactory(comedor=comedor)
    relevamiento.responsable = mock.Mock()
    relevamiento.responsable.nombre = fake.first_name()
    relevamiento.responsable.apellido = fake.last_name()
    relevamiento.responsable.mail = fake.email()
    relevamiento.responsable.celular = fake.phone_number()
    relevamiento.responsable.documento = fake.ssn()
    return relevamiento


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
    import configuraciones.templatetags.custom_filters as custom_filters

    def safe_has_group(user, group):
        if user is None:
            return False
        if not hasattr(user, "groups"):
            return False
        try:
            return user.groups.filter(name=group).exists() or getattr(
                user, "is_superuser", False
            )
        except Exception:
            return False

    monkeypatch.setattr(custom_filters, "has_group", safe_has_group)


@pytest.mark.django_db
def test_create_view_get(client_logged, comedor):
    url = reverse("relevamiento_crear", kwargs={"comedor_pk": comedor.pk})
    response = client_logged.get(url)
    assert response.status_code == 200
    assert comedor.nombre in response.content.decode()


@pytest.mark.django_db
def test_create_view_post_invalid(client_logged, comedor):
    url = reverse("relevamiento_crear", kwargs={"comedor_pk": comedor.pk})
    response = client_logged.post(url, {})
    assert response.status_code == 200
    assert not response.context["form"].is_valid()


@pytest.mark.django_db
def test_list_view(client_logged, comedor):
    url = reverse("relevamientos", kwargs={"comedor_pk": comedor.pk})
    response = client_logged.get(url)
    assert response.status_code == 200
    assert comedor.nombre in response.content.decode()


@pytest.mark.django_db
def test_detail_view(client_logged, comedor, relevamiento):
    url = reverse(
        "relevamiento_detalle", kwargs={"comedor_pk": comedor.pk, "pk": relevamiento.pk}
    )
    response = client_logged.get(url)
    assert response.status_code == 200
    assert comedor.nombre in response.content.decode()


@pytest.mark.django_db
def test_update_view_get(client_logged, comedor, relevamiento):
    url = reverse(
        "relevamiento_editar", kwargs={"comedor_pk": comedor.pk, "pk": relevamiento.pk}
    )
    response = client_logged.get(url)
    assert response.status_code == 200
    assert comedor.nombre in response.content.decode()


@pytest.mark.django_db
def test_update_view_post_invalid(client_logged, comedor, relevamiento):
    url = reverse(
        "relevamiento_editar", kwargs={"comedor_pk": comedor.pk, "pk": relevamiento.pk}
    )
    response = client_logged.post(url, {})
    assert response.status_code == 200
    assert not response.context["form"].is_valid()


@pytest.mark.django_db
def test_delete_view_get(client_logged, comedor, relevamiento):
    url = reverse(
        "relevamiento_eliminar",
        kwargs={"comedor_pk": comedor.pk, "pk": relevamiento.pk},
    )
    response = client_logged.get(url)
    assert response.status_code == 200
    assert comedor.nombre in response.content.decode()


@pytest.mark.django_db
def test_delete_view_post(client_logged, comedor, relevamiento):
    url = reverse(
        "relevamiento_eliminar",
        kwargs={"comedor_pk": comedor.pk, "pk": relevamiento.pk},
    )
    response = client_logged.post(url)
    assert response.status_code == 302
    assert response.url == reverse("comedor_detalle", kwargs={"pk": comedor.pk})
    assert not Relevamiento.objects.filter(pk=relevamiento.pk).exists()
