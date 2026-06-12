from datetime import date

import pytest
from django.contrib.auth.models import Permission, User
from django.test import Client
from django.urls import reverse

from ciudadanos.models import Ciudadano
from centrodeinfancia.models import CentroDeInfancia, NominaCentroInfancia
from core.models import Provincia
from users.models import Profile


# ─────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────

@pytest.fixture
def provincia():
    return Provincia.objects.create(nombre="Buenos Aires")


@pytest.fixture
def centro(provincia):
    return CentroDeInfancia.objects.create(nombre="CDI Girasoles", provincia=provincia)


@pytest.fixture
def ciudadano():
    return Ciudadano.objects.create(
        apellido="Ramirez",
        nombre="Sofia",
        fecha_nacimiento=date(2020, 3, 15),
        documento=44555666,
    )


@pytest.fixture
def nomina(centro, ciudadano):
    return NominaCentroInfancia.objects.create(
        centro=centro,
        ciudadano=ciudadano,
        dni=ciudadano.documento,
        apellido=ciudadano.apellido,
        nombre=ciudadano.nombre,
        fecha_nacimiento=ciudadano.fecha_nacimiento,
        estado=NominaCentroInfancia.ESTADO_ACTIVO,
    )


def _make_user(*codenames):
    user = User.objects.create_user(
        username=f"user_{'_'.join(codenames)}", password="test1234"
    )
    Profile.objects.get_or_create(user=user)
    for codename in codenames:
        try:
            user.user_permissions.add(Permission.objects.get(codename=codename))
        except Permission.DoesNotExist:
            pass
    return user


@pytest.fixture
def usuario_view():
    return _make_user("view_nominacentroinfancia", "view_centrodeinfancia")


@pytest.fixture
def usuario_add():
    return _make_user("add_nominacentroinfancia", "view_centrodeinfancia")


@pytest.fixture
def usuario_change():
    return _make_user("change_nominacentroinfancia", "view_centrodeinfancia")


_VALID_POST = {
    "estado": NominaCentroInfancia.ESTADO_ACTIVO,
    "apellido": "Ramirez",
    "nombre": "Sofia",
    "fecha_nacimiento": "2020-03-15",
    "dni": "44555666",
}


# ─────────────────────────────────────────────────────────
# Create view
# ─────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestNominaCentroInfanciaCreateView:

    def _url(self, centro):
        return reverse("centrodeinfancia_nomina_crear", kwargs={"pk": centro.pk})

    def test_requiere_autenticacion(self, centro):
        resp = Client().get(self._url(centro))
        assert resp.status_code in (302, 403)

    def test_get_sin_query_muestra_busqueda(self, usuario_add, centro):
        client = Client()
        client.force_login(usuario_add)
        resp = client.get(self._url(centro))
        assert resp.status_code == 200
        assert not resp.context.get("mostrar_formulario")

    def test_get_con_ciudadano_id_muestra_formulario(self, usuario_add, centro, ciudadano):
        client = Client()
        client.force_login(usuario_add)
        url = self._url(centro) + f"?ciudadano_id={ciudadano.pk}"
        resp = client.get(url)
        assert resp.status_code == 200
        assert resp.context.get("mostrar_formulario")
        assert resp.context.get("selected_ciudadano") == ciudadano

    def test_get_query_sin_resultados_muestra_formulario(self, usuario_add, centro):
        client = Client()
        client.force_login(usuario_add)
        url = self._url(centro) + "?query=99999999"
        resp = client.get(url)
        assert resp.status_code == 200
        assert resp.context.get("no_resultados")
        assert resp.context.get("mostrar_formulario")

    def test_get_usa_template_destinatario(self, usuario_add, centro):
        client = Client()
        client.force_login(usuario_add)
        url = self._url(centro) + "?query=99999999"
        resp = client.get(url)
        assert "centrodeinfancia/destinatario_form.html" in [
            t.name for t in resp.templates
        ]

    def test_post_crea_nomina_con_ciudadano_existente(
        self, usuario_add, centro, ciudadano
    ):
        client = Client()
        client.force_login(usuario_add)
        data = {**_VALID_POST, "ciudadano_id": ciudadano.pk}
        resp = client.post(self._url(centro), data)
        assert resp.status_code == 302
        assert NominaCentroInfancia.objects.filter(
            centro=centro, ciudadano=ciudadano
        ).exists()

    def test_post_crea_ciudadano_si_no_existe(self, usuario_add, centro):
        client = Client()
        client.force_login(usuario_add)
        data = {**_VALID_POST, "dni": "55666777", "apellido": "Nuevo", "nombre": "Niño"}
        assert not Ciudadano.objects.filter(documento="55666777").exists()
        resp = client.post(self._url(centro), data)
        assert resp.status_code == 302
        assert Ciudadano.objects.filter(documento="55666777").exists()

    def test_post_duplicado_no_crea_segunda_nomina(
        self, usuario_add, centro, ciudadano, nomina
    ):
        client = Client()
        client.force_login(usuario_add)
        data = {**_VALID_POST, "ciudadano_id": ciudadano.pk}
        resp = client.post(self._url(centro), data)
        assert resp.status_code == 302
        assert NominaCentroInfancia.objects.filter(
            centro=centro, ciudadano=ciudadano, deleted_at__isnull=True
        ).count() == 1

    def test_post_invalido_no_redirige(self, usuario_add, centro):
        client = Client()
        client.force_login(usuario_add)
        resp = client.post(self._url(centro), {"apellido": "Sin fecha"})
        assert resp.status_code == 200

    def test_contexto_incluye_centro(self, usuario_add, centro):
        client = Client()
        client.force_login(usuario_add)
        resp = client.get(self._url(centro))
        assert resp.context["centro"] == centro


# ─────────────────────────────────────────────────────────
# Edit view
# ─────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestNominaCentroInfanciaEditView:

    def _url(self, centro, nomina):
        return reverse(
            "centrodeinfancia_nomina_editar",
            kwargs={"pk": centro.pk, "nomina_id": nomina.pk},
        )

    def test_requiere_autenticacion(self, centro, nomina):
        resp = Client().get(self._url(centro, nomina))
        assert resp.status_code in (302, 403)

    def test_get_renderiza_template_destinatario(
        self, usuario_change, centro, nomina
    ):
        client = Client()
        client.force_login(usuario_change)
        resp = client.get(self._url(centro, nomina))
        assert resp.status_code == 200
        assert "centrodeinfancia/destinatario_form.html" in [
            t.name for t in resp.templates
        ]

    def test_contexto_es_edit(self, usuario_change, centro, nomina):
        client = Client()
        client.force_login(usuario_change)
        resp = client.get(self._url(centro, nomina))
        assert resp.status_code == 200
        assert resp.context["is_edit"] is True
        assert resp.context["centro"] == centro

    def test_post_actualiza_campos(self, usuario_change, centro, nomina):
        client = Client()
        client.force_login(usuario_change)
        data = {
            **_VALID_POST,
            "apellido": "Ramirez-Editado",
            "nombre": "Sofia M.",
            "estado": NominaCentroInfancia.ESTADO_BAJA,
        }
        resp = client.post(self._url(centro, nomina), data)
        assert resp.status_code == 302
        nomina.refresh_from_db()
        assert nomina.apellido == "Ramirez-Editado"
        assert nomina.estado == NominaCentroInfancia.ESTADO_BAJA

    def test_post_redirige_a_nomina(self, usuario_change, centro, nomina):
        client = Client()
        client.force_login(usuario_change)
        resp = client.post(self._url(centro, nomina), _VALID_POST)
        expected = reverse("centrodeinfancia_nomina_ver", kwargs={"pk": centro.pk})
        assert resp.status_code == 302
        assert expected in resp.url

    def test_scope_nomina_de_otro_centro_da_404(
        self, usuario_change, centro, ciudadano
    ):
        otro_centro = CentroDeInfancia.objects.create(
            nombre="CDI Otro", provincia=centro.provincia
        )
        nomina_otro = NominaCentroInfancia.objects.create(
            centro=otro_centro,
            ciudadano=ciudadano,
            dni=ciudadano.documento,
            apellido=ciudadano.apellido,
            nombre=ciudadano.nombre,
            fecha_nacimiento=ciudadano.fecha_nacimiento,
        )
        client = Client()
        client.force_login(usuario_change)
        url = reverse(
            "centrodeinfancia_nomina_editar",
            kwargs={"pk": centro.pk, "nomina_id": nomina_otro.pk},
        )
        assert client.get(url).status_code in (404, 403)


# ─────────────────────────────────────────────────────────
# Detail view
# ─────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestNominaCentroInfanciaDestinatarioDetailView:

    def _url(self, centro, nomina):
        return reverse(
            "centrodeinfancia_nomina_destinatario_ver",
            kwargs={"pk": centro.pk, "nomina_id": nomina.pk},
        )

    def test_requiere_autenticacion(self, centro, nomina):
        resp = Client().get(self._url(centro, nomina))
        assert resp.status_code in (302, 403)

    def test_get_devuelve_200(self, usuario_view, centro, nomina):
        client = Client()
        client.force_login(usuario_view)
        resp = client.get(self._url(centro, nomina))
        assert resp.status_code == 200

    def test_usa_template_destinatario_detail(self, usuario_view, centro, nomina):
        client = Client()
        client.force_login(usuario_view)
        resp = client.get(self._url(centro, nomina))
        assert "centrodeinfancia/destinatario_detail.html" in [
            t.name for t in resp.templates
        ]

    def test_contexto_contiene_nomina_y_centro(self, usuario_view, centro, nomina):
        client = Client()
        client.force_login(usuario_view)
        resp = client.get(self._url(centro, nomina))
        assert resp.context["nomina"] == nomina
        assert resp.context["centro"] == centro
        assert "puede_editar" in resp.context

    def test_scope_nomina_de_otro_centro_da_404(
        self, usuario_view, centro, ciudadano
    ):
        otro_centro = CentroDeInfancia.objects.create(
            nombre="CDI Otro", provincia=centro.provincia
        )
        nomina_otro = NominaCentroInfancia.objects.create(
            centro=otro_centro,
            ciudadano=ciudadano,
            dni=ciudadano.documento,
            apellido=ciudadano.apellido,
            nombre=ciudadano.nombre,
            fecha_nacimiento=ciudadano.fecha_nacimiento,
        )
        client = Client()
        client.force_login(usuario_view)
        url = reverse(
            "centrodeinfancia_nomina_destinatario_ver",
            kwargs={"pk": centro.pk, "nomina_id": nomina_otro.pk},
        )
        assert client.get(url).status_code in (404, 403)
