"""Tests de vistas para el módulo de comunicados."""

from datetime import timedelta
from unittest.mock import patch

import pytest
from django.contrib.auth.models import Group, User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from comunicados.models import (
    Comunicado,
    ComunicadoAdjunto,
    EstadoComunicado,
    SubtipoComunicado,
    TipoComunicado,
)
from comedores.models import Comedor
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
        fecha_publicacion=(
            timezone.now() if estado == EstadoComunicado.PUBLICADO else None
        ),
        fecha_vencimiento=fecha_vencimiento,
        usuario_creador=usuario_creador,
    )


def _comunicado_form_data(**overrides):
    data = {
        "titulo": "Comunicado de prueba",
        "cuerpo": "Contenido",
        "tipo": TipoComunicado.INTERNO,
        "subtipo": "",
        "fecha_vencimiento": "",
        "adjuntos-TOTAL_FORMS": "0",
        "adjuntos-INITIAL_FORMS": "0",
        "adjuntos-MIN_NUM_FORMS": "0",
        "adjuntos-MAX_NUM_FORMS": "1000",
    }
    data.update(overrides)
    return data


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


@pytest.mark.parametrize(
    "estado", [EstadoComunicado.BORRADOR, EstadoComunicado.ARCHIVADO]
)
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


def test_create_rollbackea_todo_si_falla_guardado_de_adjunto(client):
    admin = User.objects.create_superuser(
        "admin_create", "admin_create@test.com", "test"
    )
    client.force_login(admin)
    archivo = SimpleUploadedFile(
        "adjunto.pdf",
        b"%PDF-1.4 fake",
        content_type="application/pdf",
    )

    with patch(
        "comunicados.views.ComunicadoAdjunto.objects.create",
        side_effect=RuntimeError("fallo adjunto"),
    ):
        with pytest.raises(RuntimeError, match="fallo adjunto"):
            client.post(
                reverse("comunicados_crear"),
                data=_comunicado_form_data(
                    titulo="Atomic create",
                    archivos_adjuntos=archivo,
                ),
            )

    assert not Comunicado.objects.filter(titulo="Atomic create").exists()


def test_update_rollbackea_todo_si_falla_guardado_de_adjunto(client):
    admin = User.objects.create_superuser(
        "admin_update", "admin_update@test.com", "test"
    )
    client.force_login(admin)
    comunicado = _create_comunicado(
        usuario_creador=admin,
        estado=EstadoComunicado.BORRADOR,
    )
    archivo = SimpleUploadedFile(
        "adjunto.pdf",
        b"%PDF-1.4 fake",
        content_type="application/pdf",
    )

    with patch(
        "comunicados.views.ComunicadoAdjunto.objects.create",
        side_effect=RuntimeError("fallo adjunto"),
    ):
        with pytest.raises(RuntimeError, match="fallo adjunto"):
            client.post(
                reverse("comunicados_editar", kwargs={"pk": comunicado.pk}),
                data=_comunicado_form_data(
                    titulo="Titulo actualizado",
                    cuerpo="Contenido editado",
                    archivos_adjuntos=archivo,
                ),
            )

    comunicado.refresh_from_db()
    assert comunicado.titulo != "Titulo actualizado"


def test_listado_publico_expone_adjuntos_count(client):
    creador = _create_user("creador_adjuntos_count")
    viewer = _create_user("viewer_adjuntos_count")
    comunicado = _create_comunicado(
        usuario_creador=creador,
        estado=EstadoComunicado.PUBLICADO,
        fecha_vencimiento=timezone.now() + timedelta(days=1),
    )
    for idx in range(2):
        ComunicadoAdjunto.objects.create(
            comunicado=comunicado,
            archivo=SimpleUploadedFile(
                f"adjunto_{idx}.pdf",
                b"%PDF-1.4 test",
                content_type="application/pdf",
            ),
            nombre_original=f"adjunto_{idx}.pdf",
        )
    client.force_login(viewer)

    response = client.get(reverse("comunicados"))

    assert response.status_code == 200
    comunicado_ctx = next(
        item for item in response.context["comunicados"] if item.pk == comunicado.pk
    )
    assert comunicado_ctx.adjuntos_count == 2
    assert b"2 adjunto(s)" in response.content


def test_listado_publico_no_hace_consultas_n_mas_1_para_adjuntos(client):
    creador = _create_user("creador_nmas1")
    viewer = _create_user("viewer_nmas1")
    for idx in range(5):
        comunicado = _create_comunicado(
            usuario_creador=creador,
            estado=EstadoComunicado.PUBLICADO,
            fecha_vencimiento=timezone.now() + timedelta(days=1),
        )
        ComunicadoAdjunto.objects.create(
            comunicado=comunicado,
            archivo=SimpleUploadedFile(
                f"adjunto_{idx}.pdf",
                b"%PDF-1.4 test",
                content_type="application/pdf",
            ),
            nombre_original=f"adjunto_{idx}.pdf",
        )
    client.force_login(viewer)

    with CaptureQueriesContext(connection) as ctx:
        response = client.get(reverse("comunicados"))

    assert response.status_code == 200
    adjuntos_queries = [
        query["sql"]
        for query in ctx.captured_queries
        if "comunicados_comunicadoadjunto" in query["sql"].lower()
    ]
    assert len(adjuntos_queries) <= 2


def test_gestion_oculta_boton_editar_si_usuario_no_puede_editar(client):
    creador = _create_user("creador_no_edit")
    usuario_gestion = _create_user(
        "gestion_sin_editar",
        groups=[UserGroups.COMUNICADO_PUBLICAR],
    )
    comunicado = _create_comunicado(
        usuario_creador=creador,
        estado=EstadoComunicado.BORRADOR,
    )
    client.force_login(usuario_gestion)

    response = client.get(reverse("comunicados_gestion"))

    assert response.status_code == 200
    edit_url = reverse("comunicados_editar", kwargs={"pk": comunicado.pk})
    assert edit_url.encode() not in response.content


def test_gestion_muestra_boton_editar_si_usuario_tiene_permiso(client):
    creador = _create_user("creador_con_edit")
    usuario_gestion = _create_user(
        "gestion_con_editar",
        groups=[UserGroups.COMUNICADO_EDITAR],
    )
    comunicado = _create_comunicado(
        usuario_creador=creador,
        estado=EstadoComunicado.BORRADOR,
    )
    client.force_login(usuario_gestion)

    response = client.get(reverse("comunicados_gestion"))

    assert response.status_code == 200
    edit_url = reverse("comunicados_editar", kwargs={"pk": comunicado.pk})
    assert edit_url.encode() in response.content


def test_create_guarda_adjuntos_y_destinatarios(client):
    admin = User.objects.create_superuser(
        "admin_create_ok", "create_ok@test.com", "test"
    )
    comedor = Comedor.objects.create(nombre="Comedor create ok")
    client.force_login(admin)
    archivo = SimpleUploadedFile(
        "adjunto_create.pdf",
        b"%PDF-1.4 create",
        content_type="application/pdf",
    )

    response = client.post(
        reverse("comunicados_crear"),
        data=_comunicado_form_data(
            titulo="Create con related",
            tipo=TipoComunicado.EXTERNO,
            subtipo=SubtipoComunicado.COMEDORES,
            comedores=[str(comedor.pk)],
            archivos_adjuntos=archivo,
        ),
    )

    assert response.status_code == 302
    comunicado = Comunicado.objects.get(titulo="Create con related")
    assert comunicado.comedores.filter(pk=comedor.pk).exists()
    assert comunicado.adjuntos.count() == 1


def test_update_guarda_adjuntos_y_destinatarios(client):
    admin = User.objects.create_superuser(
        "admin_update_ok", "update_ok@test.com", "test"
    )
    comedor_a = Comedor.objects.create(nombre="Comedor A")
    comedor_b = Comedor.objects.create(nombre="Comedor B")
    comunicado = _create_comunicado(
        usuario_creador=admin,
        estado=EstadoComunicado.BORRADOR,
        tipo=TipoComunicado.EXTERNO,
    )
    comunicado.subtipo = SubtipoComunicado.COMEDORES
    comunicado.save(update_fields=["subtipo"])
    comunicado.comedores.add(comedor_a)
    client.force_login(admin)
    archivo = SimpleUploadedFile(
        "adjunto_update.pdf",
        b"%PDF-1.4 update",
        content_type="application/pdf",
    )

    response = client.post(
        reverse("comunicados_editar", kwargs={"pk": comunicado.pk}),
        data=_comunicado_form_data(
            titulo="Update con related",
            tipo=TipoComunicado.EXTERNO,
            subtipo=SubtipoComunicado.COMEDORES,
            comedores=[str(comedor_b.pk)],
            archivos_adjuntos=archivo,
        ),
    )

    assert response.status_code == 302
    comunicado.refresh_from_db()
    assert comunicado.titulo == "Update con related"
    assert list(comunicado.comedores.values_list("pk", flat=True)) == [comedor_b.pk]
    assert comunicado.adjuntos.count() == 1


def test_create_invalido_renderiza_formulario_con_errores(client):
    admin = User.objects.create_superuser("admin_invalid", "invalid@test.com", "test")
    client.force_login(admin)

    response = client.post(
        reverse("comunicados_crear"),
        data=_comunicado_form_data(titulo=""),
    )

    assert response.status_code == 200
    assert "titulo" in response.context["form"].errors
