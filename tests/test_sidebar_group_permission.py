from types import SimpleNamespace

import pytest
from django.contrib.auth.models import Permission, User
from django.template.loader import render_to_string
from django.test import RequestFactory
from django.urls import reverse


SIDEBAR_TEMPLATES = ("includes/sidebar/opciones.html",)


def _render_sidebar(template_name, user):
    request = RequestFactory().get("/inicio/")
    request.user = user
    request.resolver_match = SimpleNamespace(route="inicio")
    return render_to_string(template_name, request=request)


@pytest.mark.django_db
@pytest.mark.parametrize("template_name", SIDEBAR_TEMPLATES)
def test_sidebar_oculta_grupos_sin_permiso_especifico(template_name):
    suffix = template_name.rsplit("/", maxsplit=1)[-1].split(".", maxsplit=1)[0]
    user = User.objects.create_user(username=f"sin-grupos-{suffix}")
    user.user_permissions.add(
        Permission.objects.get(
            content_type__app_label="auth",
            codename="view_user",
        )
    )

    html = _render_sidebar(template_name, user)

    assert f'href="{reverse("grupos")}"' not in html


@pytest.mark.django_db
@pytest.mark.parametrize("template_name", SIDEBAR_TEMPLATES)
def test_sidebar_muestra_grupos_con_permiso_especifico(template_name):
    suffix = template_name.rsplit("/", maxsplit=1)[-1].split(".", maxsplit=1)[0]
    user = User.objects.create_user(username=f"con-grupos-{suffix}")
    user.user_permissions.add(
        Permission.objects.get(
            content_type__app_label="auth",
            codename="view_group",
        )
    )

    html = _render_sidebar(template_name, user)

    assert f'href="{reverse("grupos")}"' in html


@pytest.mark.django_db
def test_acceso_directo_a_grupos_sigue_protegido_sin_permiso(client):
    user = User.objects.create_user(username="grupos-directo-sin-permiso")
    user.user_permissions.add(
        Permission.objects.get(
            content_type__app_label="auth",
            codename="view_user",
        )
    )
    client.force_login(user)

    response = client.get(reverse("grupos"))

    assert response.status_code == 403
