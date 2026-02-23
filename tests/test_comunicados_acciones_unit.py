"""Tests de acciones y filtros para el módulo de comunicados."""

from datetime import timedelta

import pytest
from django.contrib.auth.models import Group, User
from django.urls import reverse
from django.utils import timezone

from comedores.models import Comedor
from comunicados.models import (
    Comunicado,
    EstadoComunicado,
    TipoComunicado,
)
from core.constants import UserGroups


pytestmark = pytest.mark.django_db


# =============================================================================
# Helpers
# =============================================================================


def _create_user(username: str, groups: list[str] | None = None) -> User:
    user = User.objects.create_user(username=username, password="testpass123")
    for group_name in groups or []:
        group, _ = Group.objects.get_or_create(name=group_name)
        user.groups.add(group)
    return user


def _create_comunicado(
    *,
    usuario_creador: User,
    estado: str = EstadoComunicado.BORRADOR,
    tipo: str = TipoComunicado.INTERNO,
    destacado: bool = False,
    fecha_vencimiento=None,
    titulo: str | None = None,
) -> Comunicado:
    return Comunicado.objects.create(
        titulo=titulo or f"Comunicado {estado}",
        cuerpo="Contenido de prueba",
        estado=estado,
        tipo=tipo,
        destacado=destacado,
        fecha_publicacion=(
            timezone.now() if estado == EstadoComunicado.PUBLICADO else None
        ),
        fecha_vencimiento=fecha_vencimiento,
        usuario_creador=usuario_creador,
    )


# =============================================================================
# Publicar
# =============================================================================


def test_publicar_borrador_cambia_estado_a_publicado(client):
    admin = User.objects.create_superuser("admin_pub", "pub@test.com", "test")
    comunicado = _create_comunicado(
        usuario_creador=admin, estado=EstadoComunicado.BORRADOR
    )
    client.force_login(admin)

    response = client.post(
        reverse("comunicados_publicar", kwargs={"pk": comunicado.pk})
    )

    assert response.status_code == 302
    comunicado.refresh_from_db()
    assert comunicado.estado == EstadoComunicado.PUBLICADO
    assert comunicado.fecha_publicacion is not None


def test_publicar_sin_permiso_devuelve_403(client):
    creador = _create_user("creador_pub_403")
    usuario_sin_permiso = _create_user(
        "sin_permiso_pub", groups=[UserGroups.COMUNICADO_CREAR]
    )
    comunicado = _create_comunicado(
        usuario_creador=creador, estado=EstadoComunicado.BORRADOR
    )
    client.force_login(usuario_sin_permiso)

    response = client.post(
        reverse("comunicados_publicar", kwargs={"pk": comunicado.pk})
    )

    assert response.status_code == 403
    comunicado.refresh_from_db()
    assert comunicado.estado == EstadoComunicado.BORRADOR


def test_publicar_ya_publicado_no_cambia_estado(client):
    admin = User.objects.create_superuser("admin_pub_dup", "pub_dup@test.com", "test")
    comunicado = _create_comunicado(
        usuario_creador=admin, estado=EstadoComunicado.PUBLICADO
    )
    fecha_original = comunicado.fecha_publicacion
    client.force_login(admin)

    client.post(reverse("comunicados_publicar", kwargs={"pk": comunicado.pk}))

    comunicado.refresh_from_db()
    assert comunicado.estado == EstadoComunicado.PUBLICADO
    assert comunicado.fecha_publicacion == fecha_original


def test_publicar_archivado_no_cambia_estado(client):
    admin = User.objects.create_superuser("admin_pub_arch", "pub_arch@test.com", "test")
    comunicado = _create_comunicado(
        usuario_creador=admin, estado=EstadoComunicado.ARCHIVADO
    )
    client.force_login(admin)

    client.post(reverse("comunicados_publicar", kwargs={"pk": comunicado.pk}))

    comunicado.refresh_from_db()
    assert comunicado.estado == EstadoComunicado.ARCHIVADO


# =============================================================================
# Archivar
# =============================================================================


def test_archivar_publicado_cambia_estado_a_archivado(client):
    admin = User.objects.create_superuser("admin_arch", "arch@test.com", "test")
    comunicado = _create_comunicado(
        usuario_creador=admin, estado=EstadoComunicado.PUBLICADO
    )
    client.force_login(admin)

    response = client.post(
        reverse("comunicados_archivar", kwargs={"pk": comunicado.pk})
    )

    assert response.status_code == 302
    comunicado.refresh_from_db()
    assert comunicado.estado == EstadoComunicado.ARCHIVADO


def test_archivar_borrador_cambia_estado_a_archivado(client):
    admin = User.objects.create_superuser(
        "admin_arch_borr", "arch_borr@test.com", "test"
    )
    comunicado = _create_comunicado(
        usuario_creador=admin, estado=EstadoComunicado.BORRADOR
    )
    client.force_login(admin)

    client.post(reverse("comunicados_archivar", kwargs={"pk": comunicado.pk}))

    comunicado.refresh_from_db()
    assert comunicado.estado == EstadoComunicado.ARCHIVADO


def test_archivar_sin_permiso_devuelve_403(client):
    creador = _create_user("creador_arch_403")
    usuario_sin_permiso = _create_user(
        "sin_permiso_arch", groups=[UserGroups.COMUNICADO_CREAR]
    )
    comunicado = _create_comunicado(
        usuario_creador=creador, estado=EstadoComunicado.PUBLICADO
    )
    client.force_login(usuario_sin_permiso)

    response = client.post(
        reverse("comunicados_archivar", kwargs={"pk": comunicado.pk})
    )

    assert response.status_code == 403
    comunicado.refresh_from_db()
    assert comunicado.estado == EstadoComunicado.PUBLICADO


def test_archivar_ya_archivado_no_cambia_estado(client):
    admin = User.objects.create_superuser("admin_arch_dup", "arch_dup@test.com", "test")
    comunicado = _create_comunicado(
        usuario_creador=admin, estado=EstadoComunicado.ARCHIVADO
    )
    client.force_login(admin)

    client.post(reverse("comunicados_archivar", kwargs={"pk": comunicado.pk}))

    comunicado.refresh_from_db()
    assert comunicado.estado == EstadoComunicado.ARCHIVADO


# =============================================================================
# Toggle Destacado
# =============================================================================


def test_toggle_destacado_activa_si_no_estaba_destacado(client):
    admin = User.objects.create_superuser("admin_tog_on", "tog_on@test.com", "test")
    comunicado = _create_comunicado(
        usuario_creador=admin, estado=EstadoComunicado.PUBLICADO, destacado=False
    )
    client.force_login(admin)

    response = client.post(
        reverse("comunicados_toggle_destacado", kwargs={"pk": comunicado.pk})
    )

    assert response.status_code == 302
    comunicado.refresh_from_db()
    assert comunicado.destacado is True


def test_toggle_destacado_desactiva_si_ya_estaba_destacado(client):
    admin = User.objects.create_superuser("admin_tog_off", "tog_off@test.com", "test")
    comunicado = _create_comunicado(
        usuario_creador=admin, estado=EstadoComunicado.PUBLICADO, destacado=True
    )
    client.force_login(admin)

    client.post(reverse("comunicados_toggle_destacado", kwargs={"pk": comunicado.pk}))

    comunicado.refresh_from_db()
    assert comunicado.destacado is False


def test_toggle_destacado_sin_permiso_devuelve_403(client):
    creador = _create_user("creador_tog_403")
    usuario_sin_permiso = _create_user(
        "sin_permiso_tog", groups=[UserGroups.COMUNICADO_CREAR]
    )
    comunicado = _create_comunicado(
        usuario_creador=creador, estado=EstadoComunicado.PUBLICADO, destacado=False
    )
    client.force_login(usuario_sin_permiso)

    response = client.post(
        reverse("comunicados_toggle_destacado", kwargs={"pk": comunicado.pk})
    )

    assert response.status_code == 403
    comunicado.refresh_from_db()
    assert comunicado.destacado is False


def test_toggle_destacado_no_aplica_a_borrador(client):
    admin = User.objects.create_superuser("admin_tog_borr", "tog_borr@test.com", "test")
    comunicado = _create_comunicado(
        usuario_creador=admin, estado=EstadoComunicado.BORRADOR, destacado=False
    )
    client.force_login(admin)

    client.post(reverse("comunicados_toggle_destacado", kwargs={"pk": comunicado.pk}))

    comunicado.refresh_from_db()
    assert comunicado.destacado is False


# =============================================================================
# Eliminar
# =============================================================================


def test_eliminar_borrador_como_admin_elimina_correctamente(client):
    admin = User.objects.create_superuser("admin_del", "del@test.com", "test")
    comunicado = _create_comunicado(
        usuario_creador=admin, estado=EstadoComunicado.BORRADOR
    )
    pk = comunicado.pk
    client.force_login(admin)

    response = client.post(reverse("comunicados_eliminar", kwargs={"pk": pk}))

    assert response.status_code == 302
    assert not Comunicado.objects.filter(pk=pk).exists()


@pytest.mark.parametrize(
    "estado", [EstadoComunicado.PUBLICADO, EstadoComunicado.ARCHIVADO]
)
def test_eliminar_no_borrador_como_admin_devuelve_403(client, estado):
    admin = User.objects.create_superuser(
        f"admin_del_{estado}", f"del_{estado}@test.com", "test"
    )
    comunicado = _create_comunicado(usuario_creador=admin, estado=estado)
    client.force_login(admin)

    response = client.post(
        reverse("comunicados_eliminar", kwargs={"pk": comunicado.pk})
    )

    assert response.status_code == 403
    assert Comunicado.objects.filter(pk=comunicado.pk).exists()


def test_eliminar_borrador_sin_ser_admin_devuelve_403(client):
    creador = _create_user("creador_del_403")
    usuario_no_admin = _create_user(
        "no_admin_del",
        groups=[UserGroups.COMUNICADO_CREAR, UserGroups.COMUNICADO_EDITAR],
    )
    comunicado = _create_comunicado(
        usuario_creador=creador, estado=EstadoComunicado.BORRADOR
    )
    client.force_login(usuario_no_admin)

    response = client.post(
        reverse("comunicados_eliminar", kwargs={"pk": comunicado.pk})
    )

    assert response.status_code == 403
    assert Comunicado.objects.filter(pk=comunicado.pk).exists()


# =============================================================================
# Filtros - Listado Público
# =============================================================================


def test_listado_publico_no_muestra_vencidos(client):
    creador = _create_user("creador_venc")
    viewer = _create_user("viewer_venc")
    vencido = _create_comunicado(
        usuario_creador=creador,
        estado=EstadoComunicado.PUBLICADO,
        titulo="Comunicado vencido",
        fecha_vencimiento=timezone.now() - timedelta(days=1),
    )
    vigente = _create_comunicado(
        usuario_creador=creador,
        estado=EstadoComunicado.PUBLICADO,
        titulo="Comunicado vigente",
        fecha_vencimiento=timezone.now() + timedelta(days=1),
    )
    client.force_login(viewer)

    response = client.get(reverse("comunicados"))

    assert response.status_code == 200
    pks = [c.pk for c in response.context["comunicados"]]
    assert vencido.pk not in pks
    assert vigente.pk in pks


def test_listado_publico_no_muestra_comunicados_externos(client):
    creador = _create_user("creador_ext_pub")
    viewer = _create_user("viewer_ext_pub")
    externo = _create_comunicado(
        usuario_creador=creador,
        estado=EstadoComunicado.PUBLICADO,
        tipo=TipoComunicado.EXTERNO,
        titulo="Comunicado externo",
    )
    interno = _create_comunicado(
        usuario_creador=creador,
        estado=EstadoComunicado.PUBLICADO,
        tipo=TipoComunicado.INTERNO,
        titulo="Comunicado interno",
    )
    client.force_login(viewer)

    response = client.get(reverse("comunicados"))

    pks = [c.pk for c in response.context["comunicados"]]
    assert externo.pk not in pks
    assert interno.pk in pks


def test_listado_publico_filtra_por_titulo(client):
    creador = _create_user("creador_titulo_pub")
    viewer = _create_user("viewer_titulo_pub")
    _create_comunicado(
        usuario_creador=creador,
        estado=EstadoComunicado.PUBLICADO,
        titulo="Nota de seguridad alimentaria",
    )
    _create_comunicado(
        usuario_creador=creador,
        estado=EstadoComunicado.PUBLICADO,
        titulo="Circular administrativa",
    )
    client.force_login(viewer)

    response = client.get(reverse("comunicados") + "?titulo=seguridad")

    assert response.status_code == 200
    resultados = list(response.context["comunicados"])
    assert len(resultados) == 1
    assert "seguridad" in resultados[0].titulo.lower()


def test_listado_publico_con_estado_archivado_muestra_archivados(client):
    creador = _create_user("creador_arch_pub")
    viewer = _create_user("viewer_arch_pub")
    archivado = _create_comunicado(
        usuario_creador=creador,
        estado=EstadoComunicado.ARCHIVADO,
        titulo="Comunicado archivado",
    )
    publicado = _create_comunicado(
        usuario_creador=creador,
        estado=EstadoComunicado.PUBLICADO,
        titulo="Comunicado publicado",
    )
    client.force_login(viewer)

    response = client.get(reverse("comunicados") + "?estado=archivado")

    pks = [c.pk for c in response.context["comunicados"]]
    assert archivado.pk in pks
    assert publicado.pk not in pks


def test_listado_publico_destacados_aparecen_primero(client):
    creador = _create_user("creador_dest_ord")
    viewer = _create_user("viewer_dest_ord")
    normal = _create_comunicado(
        usuario_creador=creador,
        estado=EstadoComunicado.PUBLICADO,
        titulo="Normal",
        destacado=False,
    )
    destacado = _create_comunicado(
        usuario_creador=creador,
        estado=EstadoComunicado.PUBLICADO,
        titulo="Destacado",
        destacado=True,
    )
    client.force_login(viewer)

    response = client.get(reverse("comunicados"))

    resultados = list(response.context["comunicados"])
    pks = [c.pk for c in resultados]
    assert pks.index(destacado.pk) < pks.index(normal.pk)


# =============================================================================
# Filtros - Gestión
# =============================================================================


def test_gestion_sin_permisos_devuelve_403(client):
    usuario_sin_permisos = _create_user("sin_permisos_gestion")
    client.force_login(usuario_sin_permisos)

    response = client.get(reverse("comunicados_gestion"))

    assert response.status_code == 403


def test_gestion_filtra_por_titulo(client):
    admin = User.objects.create_superuser("admin_gest_tit", "gest_tit@test.com", "test")
    _create_comunicado(usuario_creador=admin, titulo="Informe nutricional mayo")
    _create_comunicado(usuario_creador=admin, titulo="Circular de vacaciones")
    client.force_login(admin)

    response = client.get(reverse("comunicados_gestion") + "?titulo=nutricional")

    assert response.status_code == 200
    resultados = list(response.context["comunicados"])
    assert len(resultados) == 1
    assert "nutricional" in resultados[0].titulo.lower()


def test_gestion_filtra_por_estado(client):
    admin = User.objects.create_superuser("admin_gest_est", "gest_est@test.com", "test")
    borrador = _create_comunicado(
        usuario_creador=admin,
        estado=EstadoComunicado.BORRADOR,
        titulo="Borrador filtro",
    )
    publicado = _create_comunicado(
        usuario_creador=admin,
        estado=EstadoComunicado.PUBLICADO,
        titulo="Publicado filtro",
    )
    client.force_login(admin)

    response = client.get(
        reverse("comunicados_gestion") + f"?estado={EstadoComunicado.BORRADOR}"
    )

    pks = [c.pk for c in response.context["comunicados"]]
    assert borrador.pk in pks
    assert publicado.pk not in pks


def test_gestion_filtra_por_tipo(client):
    admin = User.objects.create_superuser(
        "admin_gest_tipo", "gest_tipo@test.com", "test"
    )
    interno = _create_comunicado(
        usuario_creador=admin, tipo=TipoComunicado.INTERNO, titulo="Interno filtro"
    )
    externo = _create_comunicado(
        usuario_creador=admin, tipo=TipoComunicado.EXTERNO, titulo="Externo filtro"
    )
    client.force_login(admin)

    response = client.get(
        reverse("comunicados_gestion") + f"?tipo={TipoComunicado.EXTERNO}"
    )

    pks = [c.pk for c in response.context["comunicados"]]
    assert externo.pk in pks
    assert interno.pk not in pks


def test_gestion_muestra_boton_destacado_solo_para_internos_publicados(client):
    admin = User.objects.create_superuser("admin_dest_btn", "dest_btn@test.com", "test")
    interno = _create_comunicado(
        usuario_creador=admin,
        estado=EstadoComunicado.PUBLICADO,
        tipo=TipoComunicado.INTERNO,
        titulo="Interno publicado",
    )
    externo = _create_comunicado(
        usuario_creador=admin,
        estado=EstadoComunicado.PUBLICADO,
        tipo=TipoComunicado.EXTERNO,
        titulo="Externo publicado",
    )
    client.force_login(admin)

    response = client.get(reverse("comunicados_gestion"))

    url_toggle_interno = reverse(
        "comunicados_toggle_destacado", kwargs={"pk": interno.pk}
    ).encode()
    url_toggle_externo = reverse(
        "comunicados_toggle_destacado", kwargs={"pk": externo.pk}
    ).encode()
    assert url_toggle_interno in response.content
    assert url_toggle_externo not in response.content


def test_gestion_comunicado_sin_vencer_con_vencimiento_nulo_aparece(client):
    admin = User.objects.create_superuser("admin_sin_venc", "sin_venc@test.com", "test")
    sin_vencimiento = _create_comunicado(
        usuario_creador=admin,
        estado=EstadoComunicado.PUBLICADO,
        titulo="Sin fecha vencimiento",
        fecha_vencimiento=None,
    )
    client.force_login(admin)

    response = client.get(reverse("comunicados"))

    pks = [c.pk for c in response.context["comunicados"]]
    assert sin_vencimiento.pk in pks


def test_gestion_no_muestra_toggle_destacado_para_borrador(client):
    admin = User.objects.create_superuser(
        "admin_tog_borr2", "tog_borr2@test.com", "test"
    )
    borrador = _create_comunicado(
        usuario_creador=admin,
        estado=EstadoComunicado.BORRADOR,
        tipo=TipoComunicado.INTERNO,
        titulo="Borrador no toggle",
    )
    client.force_login(admin)

    response = client.get(reverse("comunicados_gestion"))

    url_toggle = reverse(
        "comunicados_toggle_destacado", kwargs={"pk": borrador.pk}
    ).encode()
    assert url_toggle not in response.content
