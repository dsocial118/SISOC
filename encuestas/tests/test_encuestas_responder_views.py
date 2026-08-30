import pytest
from django.urls import reverse

from encuestas.models import (
    Pregunta,
    RecordatorioUsuario,
    RespuestaRonda,
    TipoPregunta,
    TipoSegmentacion,
)
from encuestas.services import actualizar_segmentacion, crear_encuesta, publicar


@pytest.fixture
def usuario_creador(django_user_model):
    return django_user_model.objects.create_user(username="creador", password="x")


@pytest.fixture
def respondiente(django_user_model):
    return django_user_model.objects.create_user(
        username="respondiente", password="test1234"
    )


@pytest.fixture
def ronda_todos(usuario_creador):
    encuesta = crear_encuesta(
        usuario=usuario_creador,
        titulo="Satisfacción",
        es_obligatoria=True,
        duracion_ronda_dias=7,
    )
    Pregunta.objects.create(
        encuesta=encuesta, texto="¿Todo bien?", tipo=TipoPregunta.SI_NO
    )
    actualizar_segmentacion(encuesta, tipo=TipoSegmentacion.TODOS_LOS_USUARIOS)
    return publicar(encuesta, usuario=usuario_creador)


@pytest.mark.django_db
def test_modal_aparece_en_cualquier_pagina_con_ronda_pendiente(
    client, respondiente, ronda_todos
):
    client.force_login(respondiente)
    response = client.get(reverse("inicio"))
    assert response.status_code == 200
    assert b"modal-encuesta-pendiente" in response.content


@pytest.mark.django_db
def test_modal_no_aparece_sin_ronda_pendiente(client, respondiente):
    client.force_login(respondiente)
    response = client.get(reverse("inicio"))
    assert response.status_code == 200
    assert b"modal-encuesta-pendiente" not in response.content


@pytest.mark.django_db
def test_responder_ronda_exitoso_redirige_a_next(client, respondiente, ronda_todos):
    pregunta = ronda_todos.encuesta.preguntas.get()
    client.force_login(respondiente)
    response = client.post(
        reverse("encuestas_responder", args=[ronda_todos.pk]),
        {f"respuesta-{pregunta.pk}": "si", "next": "/algun-lugar/"},
    )
    assert response.status_code == 302
    assert response.url == "/algun-lugar/"
    assert RespuestaRonda.objects.filter(
        ronda=ronda_todos, usuario=respondiente
    ).exists()


@pytest.mark.django_db
def test_responder_ronda_rechaza_next_externo(client, respondiente, ronda_todos):
    pregunta = ronda_todos.encuesta.preguntas.get()
    client.force_login(respondiente)
    response = client.post(
        reverse("encuestas_responder", args=[ronda_todos.pk]),
        {f"respuesta-{pregunta.pk}": "si", "next": "https://evil.example.com/"},
    )
    assert response.status_code == 302
    assert response.url == reverse("inicio")


@pytest.mark.django_db
def test_responder_ronda_sin_respuesta_obligatoria_no_falla_la_request(
    client, respondiente, ronda_todos
):
    client.force_login(respondiente)
    response = client.post(
        reverse("encuestas_responder", args=[ronda_todos.pk]), {"next": "/x/"}
    )
    assert response.status_code == 302
    assert not RespuestaRonda.objects.filter(
        ronda=ronda_todos, usuario=respondiente
    ).exists()


@pytest.mark.django_db
def test_responder_ronda_requiere_login(client, ronda_todos):
    response = client.post(reverse("encuestas_responder", args=[ronda_todos.pk]), {})
    assert response.status_code == 302
    assert reverse("login") in response.url


@pytest.mark.django_db
def test_posponer_ronda_view(client, respondiente, usuario_creador):
    encuesta = crear_encuesta(
        usuario=usuario_creador,
        titulo="No obligatoria",
        es_obligatoria=False,
        intervalo_recordatorio_dias=2,
        duracion_ronda_dias=7,
    )
    Pregunta.objects.create(
        encuesta=encuesta, texto="¿Todo bien?", tipo=TipoPregunta.SI_NO
    )
    actualizar_segmentacion(encuesta, tipo=TipoSegmentacion.TODOS_LOS_USUARIOS)
    ronda = publicar(encuesta, usuario=usuario_creador)

    client.force_login(respondiente)
    response = client.post(
        reverse("encuestas_responder_mas_tarde", args=[ronda.pk]), {"next": "/x/"}
    )
    assert response.status_code == 302
    assert RecordatorioUsuario.objects.filter(
        ronda=ronda, usuario=respondiente
    ).exists()
