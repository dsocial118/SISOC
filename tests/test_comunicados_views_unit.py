"""Tests de vistas para el módulo de comunicados."""

from datetime import timedelta

import pytest
from django.contrib.auth.models import Group, User
from django.urls import reverse
from django.utils import timezone

from comunicados.models import Comunicado, EstadoComunicado, TipoComunicado
from core.constants import UserGroups


pytestmark = pytest.mark.django_db


def _create_user(username: str, groups: list[str] | None = None) -> User:
    user = User.objects.create_user(username=username, password="testpass123")
    for group_name in groups or []:
        group, _ = Group.objects.get_or_create(name=group_name)
        user.groups.add(group)
    return user


def _create_comunicado(
    *,
    usuario_creador: User,
    estado: str,
    tipo: str = TipoComunicado.INTERNO,
    fecha_vencimiento=None,
) -> Comunicado:
    return Comunicado.objects.create(
        titulo=f"Comunicado {estado}",
        cuerpo="Contenido de prueba",
        estado=estado,
        tipo=tipo,
        fecha_publicacion=timezone.now() if estado == EstadoComunicado.PUBLICADO else None,
        fecha_vencimiento=fecha_vencimiento,
        usuario_creador=usuario_creador,
    )


def test_detail_permite_no_gestion_para_publicado_interno(client):
    creador = _create_user("creador_publicado")
    viewer = _create_user("viewer_publicado")
    comunicado = _create_comunicado(
        usuario_creador=creador,
        estado=EstadoComunicado.PUBLICADO,
        fecha_vencimiento=timezone.now() + timedelta(days=1),
    )
    client.force_login(viewer)

    response = client.get(reverse("comunicados_ver", kwargs={"pk": comunicado.pk}))

    assert response.status_code == 200
    assert comunicado.titulo.encode() in response.content


@pytest.mark.parametrize("estado", [EstadoComunicado.BORRADOR, EstadoComunicado.ARCHIVADO])
def test_detail_bloquea_no_gestion_para_no_publicados(client, estado):
    creador = _create_user(f"creador_{estado}")
    viewer = _create_user(f"viewer_{estado}")
    comunicado = _create_comunicado(usuario_creador=creador, estado=estado)
    client.force_login(viewer)

    response = client.get(reverse("comunicados_ver", kwargs={"pk": comunicado.pk}))

    assert response.status_code == 404


def test_detail_permite_gestion_para_borrador(client):
    creador = _create_user("creador_borrador")
    manager = _create_user("manager_borrador", groups=[UserGroups.COMUNICADO_EDITAR])
    comunicado = _create_comunicado(
        usuario_creador=creador,
        estado=EstadoComunicado.BORRADOR,
    )
    client.force_login(manager)

    response = client.get(reverse("comunicados_ver", kwargs={"pk": comunicado.pk}))

    assert response.status_code == 200
