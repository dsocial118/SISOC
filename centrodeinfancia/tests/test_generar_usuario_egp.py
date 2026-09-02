import pytest
from django.contrib.auth.models import Group, User
from django.urls import reverse

from core.constants import UserGroups


URL = "/simepi/egp/generar-usuario/"


@pytest.fixture(autouse=True)
def _grupos_simepi(db):
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


@pytest.mark.django_db
def test_ruta_legacy_de_alta_egp_redirige_al_abm_general(client):
    actor = _usuario_con_grupo("equipo-nacional", UserGroups.SIMEPI_EQUIPO_NACIONAL)
    client.force_login(actor)

    response = client.get(URL)

    assert response.status_code == 302
    assert response.url == reverse("usuario_crear")


@pytest.mark.django_db
def test_post_legacy_no_crea_usuario_y_redirige_al_abm_general(client):
    actor = _usuario_con_grupo(
        "equipo-nacional-post", UserGroups.SIMEPI_EQUIPO_NACIONAL
    )
    client.force_login(actor)

    response = client.post(
        URL,
        {
            "first_name": "Ana",
            "last_name": "Pérez",
            "email": "no-crear@example.com",
            "provincia": "1",
        },
    )

    assert response.status_code == 302
    assert response.url == reverse("usuario_crear")
    assert not User.objects.filter(email="no-crear@example.com").exists()


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
def test_sin_autenticacion_recibe_403(client):
    response = client.get(URL)

    assert response.status_code == 403
