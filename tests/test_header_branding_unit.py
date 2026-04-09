import pytest
from django.contrib.auth.models import Group, User
from django.urls import reverse


pytestmark = pytest.mark.django_db


def test_inicio_usa_logo_inet_para_grupos_vat(client):
    group, _ = Group.objects.get_or_create(name="CFPINET")
    user = User.objects.create_user(username="inet-logo", password="test1234")
    user.groups.add(group)

    client.force_login(user)
    response = client.get(reverse("inicio"))

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert "custom/img/LOGOS-INET-SE_BLANCO.png" in content
    assert "custom/img/loginPresentacion.svg" not in content
    assert "custom/img/logoBlanco.png" in content
    assert "inicio-presentacion--inet" in content
    assert "inicio-presentacion__inet-card" in content


def test_inicio_mantiene_presentacion_default_para_usuario_sin_grupo_vat(client):
    user = User.objects.create_user(username="default-logo", password="test1234")

    client.force_login(user)
    response = client.get(reverse("inicio"))

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert "custom/img/LOGOS-INET-SE_BLANCO.png" not in content
    assert "custom/img/logoBlanco.png" in content
    assert "inicio-presentacion--default" in content
    assert "inicio-presentacion__inet-card" not in content
