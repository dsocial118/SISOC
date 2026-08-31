"""Regresiones de autorización para el issue #2225."""

import pytest
from django.contrib.auth.models import Permission
from django.urls import reverse

from users.bootstrap.groups_seed import permission_codes_for_bootstrap_group


pytestmark = pytest.mark.django_db


def _permission(app_label, codename):
    return Permission.objects.get(
        content_type__app_label=app_label,
        codename=codename,
    )


def test_historia_social_requiere_permiso_de_lectura(client, user):
    client.force_login(user)

    response = client.get(reverse("ciudadanos"))

    assert response.status_code == 403


def test_historia_social_permite_lectura_con_permiso(client, user):
    user.user_permissions.add(_permission("ciudadanos", "view_ciudadano"))
    client.force_login(user)

    response = client.get(reverse("ciudadanos"))

    assert response.status_code == 200


def test_busqueda_de_ciudadanos_requiere_permiso_de_lectura(client, user):
    client.force_login(user)

    response = client.get(reverse("api_buscar_ciudadanos"), {"q": "Perez"})

    assert response.status_code == 403


def test_acompanamiento_no_admite_solo_permiso_de_comedores(client, user):
    user.user_permissions.add(_permission("comedores", "view_comedor"))
    client.force_login(user)

    response = client.get(reverse("lista_comedores_acompanamiento"))

    assert response.status_code == 403


def test_acompanamiento_permite_su_permiso_especifico(client, user):
    user.user_permissions.add(
        _permission("acompanamientos", "view_informacionrelevante")
    )
    client.force_login(user)

    response = client.get(reverse("lista_comedores_acompanamiento"))

    assert response.status_code == 200


def test_restaurar_hito_requiere_rol_tecnico_y_permiso_de_edicion(client, user):
    user.user_permissions.add(
        _permission("acompanamientos", "view_informacionrelevante")
    )
    client.force_login(user)

    response = client.post(reverse("restaurar_hito", kwargs={"comedor_id": 1}))

    assert response.status_code == 403


@pytest.mark.parametrize("group_name", ["Comedores total", "Comedores Visualización"])
def test_grupos_de_comedores_no_otorgan_acompanamiento(group_name):
    permission_codes = permission_codes_for_bootstrap_group(group_name)

    assert "acompanamientos.view_informacionrelevante" not in permission_codes
    assert "auth.role_acompanamiento_listar" not in permission_codes
    assert "auth.role_acompanamiento_detalle" not in permission_codes
