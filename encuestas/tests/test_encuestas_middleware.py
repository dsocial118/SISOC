import pytest
from django.contrib.auth.models import Permission
from django.urls import reverse

from encuestas.models import Pregunta, TipoPregunta, TipoSegmentacion
from encuestas.services import actualizar_segmentacion, crear_encuesta, publicar


@pytest.fixture
def usuario_creador(django_user_model):
    return django_user_model.objects.create_user(username="creador", password="x")


@pytest.fixture
def usuario(django_user_model):
    return django_user_model.objects.create_user(username="cualquiera", password="x")


def _publicar_encuesta(usuario_creador, *, obligatoria):
    encuesta = crear_encuesta(
        usuario=usuario_creador,
        titulo="Satisfacción",
        es_obligatoria=obligatoria,
        intervalo_recordatorio_dias=None if obligatoria else 3,
        duracion_ronda_dias=7,
    )
    Pregunta.objects.create(
        encuesta=encuesta, texto="¿Todo bien?", tipo=TipoPregunta.SI_NO
    )
    actualizar_segmentacion(encuesta, tipo=TipoSegmentacion.TODOS_LOS_USUARIOS)
    return publicar(encuesta, usuario=usuario_creador)


@pytest.mark.django_db
def test_no_bloquea_sin_ronda_pendiente(client, usuario):
    client.force_login(usuario)
    response = client.get(reverse("inicio"))
    assert response.status_code == 200


@pytest.mark.django_db
def test_no_bloquea_ronda_pendiente_no_obligatoria(client, usuario, usuario_creador):
    _publicar_encuesta(usuario_creador, obligatoria=False)
    client.force_login(usuario)
    response = client.get(reverse("inicio"))
    assert response.status_code == 200


@pytest.mark.django_db
def test_bloquea_y_redirige_a_inicio_con_ronda_obligatoria_pendiente(
    client, usuario, usuario_creador
):
    _publicar_encuesta(usuario_creador, obligatoria=True)
    client.force_login(usuario)

    response = client.get(reverse("encuestas_listar"))

    assert response.status_code == 302
    assert response.url == reverse("inicio")


@pytest.mark.django_db
def test_no_bloquea_la_pagina_de_inicio_para_evitar_loop(
    client, usuario, usuario_creador
):
    _publicar_encuesta(usuario_creador, obligatoria=True)
    client.force_login(usuario)

    response = client.get(reverse("inicio"))

    assert response.status_code == 200


@pytest.mark.django_db
def test_gestor_creador_puede_gestionar_su_encuesta_obligatoria_pendiente(
    client, usuario_creador
):
    _publicar_encuesta(usuario_creador, obligatoria=True)
    permisos = Permission.objects.filter(
        content_type__app_label="encuestas",
        codename__in=["change_encuesta", "view_encuesta"],
    )
    usuario_creador.user_permissions.add(*permisos)
    client.force_login(usuario_creador)

    response = client.get(reverse("encuestas_listar"))

    assert response.status_code == 200


@pytest.mark.django_db
def test_no_bloquea_el_endpoint_de_responder(client, usuario, usuario_creador):
    ronda = _publicar_encuesta(usuario_creador, obligatoria=True)
    client.force_login(usuario)

    response = client.post(reverse("encuestas_responder", args=[ronda.pk]), {})

    # No debe ser un 302 hacia 'inicio' por el middleware; el propio
    # ResponderRondaView redirige a next/inicio como parte de su flujo normal.
    assert response.status_code == 302


@pytest.mark.django_db
def test_no_bloquea_estaticos(client, usuario, usuario_creador):
    _publicar_encuesta(usuario_creador, obligatoria=True)
    client.force_login(usuario)

    response = client.get("/static/custom/js/encuestaPendienteModal.js")

    assert response.status_code != 302


@pytest.mark.django_db
def test_no_bloquea_a_usuario_anonimo(client, usuario_creador):
    _publicar_encuesta(usuario_creador, obligatoria=True)
    response = client.get(reverse("login"))
    assert response.status_code == 200


@pytest.mark.django_db
def test_no_hace_loop_con_cambio_de_contrasena_obligatorio(
    client, usuario, usuario_creador
):
    """Regresión: un usuario con must_change_password=True *y* una ronda
    obligatoria pendiente no debe quedar en loop entre /password/first-change/
    e 'inicio' (FirstLoginPasswordChangeMiddleware corre antes que este
    middleware y tiene prioridad, ver docstring de la clase)."""
    _publicar_encuesta(usuario_creador, obligatoria=True)
    usuario.profile.must_change_password = True
    usuario.profile.save(update_fields=["must_change_password"])
    client.force_login(usuario)

    response = client.get(reverse("password_change_required"))

    assert response.status_code == 200


@pytest.mark.django_db
def test_deja_de_bloquear_despues_de_responder(client, usuario, usuario_creador):
    ronda = _publicar_encuesta(usuario_creador, obligatoria=True)
    pregunta = ronda.encuesta.preguntas.get()
    client.force_login(usuario)

    bloqueado = client.get(reverse("encuestas_listar"))
    assert bloqueado.status_code == 302

    client.post(
        reverse("encuestas_responder", args=[ronda.pk]),
        {f"respuesta-{pregunta.pk}": "si"},
    )

    libre = client.get(reverse("inicio"))
    assert libre.status_code == 200
