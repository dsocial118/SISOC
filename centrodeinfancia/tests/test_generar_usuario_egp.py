import pytest
from django.contrib.auth.models import Group, User

from core.constants import UserGroups
from core.models import Provincia
from users.models import ProfileTerritorialScope


URL = "/simepi/egp/generar-usuario/"


@pytest.fixture(autouse=True)
def _grupos_simepi(db):
    """Las data migrations no corren en tests (TEST MIGRATE=False)."""
    for nombre in (
        UserGroups.SIMEPI_EQUIPO_NACIONAL,
        UserGroups.SIMEPI_EGP,
        UserGroups.SIMEPI_ANALISTA_DATOS,
    ):
        Group.objects.get_or_create(name=nombre)


def _usuario_con_grupo(username, grupo_nombre):
    user = User.objects.create_user(username=username, password="test1234")
    user.groups.add(Group.objects.get(name=grupo_nombre))
    return user


def _datos_validos(provincia, email):
    return {
        "first_name": "Ana",
        "last_name": "Pérez",
        "email": email,
        "provincia": provincia.pk,
    }


@pytest.mark.django_db
def test_equipo_nacional_puede_crear_egp_con_scope_provincial(client):
    provincia = Provincia.objects.create(nombre="Chaco")
    actor = _usuario_con_grupo(
        "equipo-nacional", UserGroups.SIMEPI_EQUIPO_NACIONAL
    )
    client.force_login(actor)

    assert client.get(URL).status_code == 200

    response = client.post(URL, _datos_validos(provincia, "egp@example.com"))

    assert response.status_code == 200
    nuevo = User.objects.get(email="egp@example.com")
    assert nuevo.groups.filter(name=UserGroups.SIMEPI_EGP).exists()
    assert nuevo.is_staff is True
    nuevo.profile.refresh_from_db()
    assert nuevo.profile.es_usuario_provincial is True
    scopes = ProfileTerritorialScope.objects.filter(profile=nuevo.profile)
    assert scopes.count() == 1
    scope = scopes.get()
    assert scope.provincia_id == provincia.pk
    assert scope.municipio_id is None
    assert scope.localidad_id is None


@pytest.mark.django_db
def test_superuser_puede_crear_egp(client):
    provincia = Provincia.objects.create(nombre="Formosa")
    actor = User.objects.create_superuser(
        username="superuser-egp",
        email="superuser@example.com",
        password="test1234",
    )
    client.force_login(actor)

    response = client.post(URL, _datos_validos(provincia, "egp-su@example.com"))

    assert response.status_code == 200
    assert User.objects.get(email="egp-su@example.com").groups.filter(
        name=UserGroups.SIMEPI_EGP
    ).exists()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "grupo_nombre",
    [UserGroups.SIMEPI_EGP, UserGroups.SIMEPI_ANALISTA_DATOS],
)
def test_actor_no_autorizado_recibe_403(client, grupo_nombre):
    actor = _usuario_con_grupo(f"actor-{grupo_nombre}", grupo_nombre)
    client.force_login(actor)

    assert client.get(URL).status_code == 403


@pytest.mark.django_db
def test_formulario_sin_provincia_no_crea_usuario(client):
    actor = _usuario_con_grupo(
        "equipo-nacional-invalido", UserGroups.SIMEPI_EQUIPO_NACIONAL
    )
    client.force_login(actor)

    response = client.post(
        URL,
        {
            "first_name": "Sin",
            "last_name": "Provincia",
            "email": "sin-provincia@example.com",
        },
    )

    assert response.status_code == 200
    assert "provincia" in response.context["form"].errors
    assert not User.objects.filter(email="sin-provincia@example.com").exists()


@pytest.mark.django_db
def test_post_sin_autenticacion_no_crea_usuario(client):
    provincia = Provincia.objects.create(nombre="Neuquén")

    response = client.post(
        URL,
        _datos_validos(provincia, "anonimo-egp@example.com"),
    )

    assert response.status_code in (302, 403)
    assert not User.objects.filter(email="anonimo-egp@example.com").exists()
