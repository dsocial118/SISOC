# pylint: disable=redefined-outer-name
from decimal import Decimal
import pytest

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.messages import get_messages
from django.urls import reverse

from prestaciones.models import Prestacion


User = get_user_model()


@pytest.fixture(autouse=True)
def disable_debug_tools(settings):
    """Ensure debug toolbars/middleware don't interfere with tests."""
    settings.DEBUG = False
    mw = list(settings.MIDDLEWARE)
    for m in [
        "debug_toolbar.middleware.DebugToolbarMiddleware",
        "silk.middleware.SilkyMiddleware",
    ]:
        if m in mw:
            mw.remove(m)
    settings.MIDDLEWARE = mw


@pytest.fixture(autouse=True)
def mute_historial(monkeypatch):
    # Avoid JSON serialization and external side effects from historial logging
    try:
        from historial.services.historial_service import HistorialService

        monkeypatch.setattr(
            HistorialService,
            "registrar_historial",
            staticmethod(lambda **kwargs: None),
        )
    except Exception:
        # If historial app isn't available, ignore
        pass


@pytest.fixture
def prestacion_group(db):
    group, _ = Group.objects.get_or_create(name="Gestor prestaciones")
    return group


@pytest.fixture
def user_in_group(db, prestacion_group):
    user = User.objects.create_user(username="user1", password="pass12345")
    user.groups.add(prestacion_group)
    return user


@pytest.fixture
def superuser(db):
    return User.objects.create_superuser(
        username="admin", password="adminpass", email="admin@example.com"
    )


@pytest.fixture
def prestacion(db, user_in_group):
    return Prestacion.objects.create(
        programa="Programa A",
        desayuno_valor=Decimal("10.00"),
        almuerzo_valor=Decimal("20.00"),
        merienda_valor=Decimal("5.50"),
        cena_valor=Decimal("15.00"),
        usuario_creador=user_in_group,
    )


class TestPermissions:
    def test_anonymous_access_is_forbidden(self, client):
        url = reverse("prestacion")
        resp = client.get(url)
        assert resp.status_code == 403

    def test_logged_in_without_group_forbidden(self, client, db):
        User.objects.create_user(username="nogroup", password="x")
        client.login(username="nogroup", password="x")
        resp = client.get(reverse("prestacion"))
        assert resp.status_code == 403

    def test_superuser_has_access(self, client, superuser):
        client.login(username="admin", password="adminpass")
        resp = client.get(reverse("prestacion"))
        assert resp.status_code == 200


class TestListView:
    def test_list_renders_and_paginates(self, client, user_in_group):
        client.login(username="user1", password="pass12345")
        # create 12 prestaciones for pagination (paginate_by=10)
        for i in range(12):
            Prestacion.objects.create(
                programa=f"Prog {i}", usuario_creador=user_in_group
            )

        resp = client.get(reverse("prestacion"))
        assert resp.status_code == 200
        assert "prestaciones" in resp.context
        assert len(resp.context["prestaciones"]) == 10

        resp_page2 = client.get(reverse("prestacion"), {"page": 2})
        assert resp_page2.status_code == 200
        assert len(resp_page2.context["prestaciones"]) == 2


class TestCreateView:
    def test_get_create_form(self, client, user_in_group):
        client.login(username="user1", password="pass12345")
        resp = client.get(reverse("prestacion_crear"))
        assert resp.status_code == 200
        assert "form" in resp.context

    def test_post_creates_prestacion_and_sets_usuario_creador(
        self, client, user_in_group
    ):
        client.login(username="user1", password="pass12345")
        payload = {
            "programa": "Nuevo Programa",
            "desayuno_valor": "11.11",
            "almuerzo_valor": "22.22",
            "merienda_valor": "3.33",
            "cena_valor": "44.44",
        }
        resp = client.post(reverse("prestacion_crear"), data=payload, follow=True)
        assert resp.status_code == 200

        obj = Prestacion.objects.get(programa="Nuevo Programa")
        assert obj.usuario_creador.username == "user1"

        messages_list = [m.message for m in get_messages(resp.wsgi_request)]
        assert any("creada correctamente" in m for m in messages_list)


class TestUpdateView:
    def test_update_changes_fields(self, client, prestacion, user_in_group):
        client.login(username="user1", password="pass12345")
        url = reverse("prestacion_editar", args=[prestacion.id])
        resp = client.post(
            url,
            data={
                "programa": "Programa Editado",
                "desayuno_valor": "12.00",
                "almuerzo_valor": "21.00",
                "merienda_valor": "6.00",
                "cena_valor": "16.00",
            },
            follow=True,
        )
        assert resp.status_code == 200
        prestacion.refresh_from_db()
        assert prestacion.programa == "Programa Editado"
        assert prestacion.desayuno_valor == Decimal("12.00")


class TestDetailView:
    def test_detail_renders_object(self, client, prestacion, user_in_group):
        client.login(username="user1", password="pass12345")
        resp = client.get(reverse("prestacion_detalle", args=[prestacion.id]))
        assert resp.status_code == 200
        assert "prestacion" in resp.context
        assert resp.context["prestacion"].id == prestacion.id


class TestDeleteView:
    def test_delete_confirm_context(self, client, prestacion, user_in_group):
        client.login(username="user1", password="pass12345")
        resp = client.get(reverse("prestacion_eliminar", args=[prestacion.id]))
        assert resp.status_code == 200
        # Template context expected by prestacion_confirm_delete.html
        assert "object_title" in resp.context
        assert "delete_message" in resp.context
        assert "cancel_url" in resp.context
        assert "breadcrumb_items" in resp.context

    def test_delete_removes_and_redirects_with_message(
        self, client, prestacion, user_in_group
    ):
        client.login(username="user1", password="pass12345")
        url = reverse("prestacion_eliminar", args=[prestacion.id])
        resp = client.post(url, follow=True)
        assert resp.status_code == 200
        assert not Prestacion.objects.filter(id=prestacion.id).exists()
        messages_list = [m.message for m in get_messages(resp.wsgi_request)]
        assert any("eliminada correctamente" in m for m in messages_list)


class TestForm:
    def test_form_fields_present(self):
        from prestaciones.forms import PrestacionForm

        form = PrestacionForm()
        expected = {
            "programa",
            "desayuno_valor",
            "almuerzo_valor",
            "merienda_valor",
            "cena_valor",
        }
        assert expected.issubset(set(form.fields.keys()))

    def test_form_validation(self):
        from prestaciones.forms import PrestacionForm

        form = PrestacionForm(
            data={
                "programa": "X",
                "desayuno_valor": "1.00",
                "almuerzo_valor": "2.00",
                "merienda_valor": "3.00",
                "cena_valor": "4.00",
            }
        )
        assert form.is_valid()
