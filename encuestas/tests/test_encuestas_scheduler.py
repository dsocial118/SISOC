from datetime import timedelta

import pytest
from django.core.management import call_command
from django.utils import timezone

from encuestas.models import EstadoRonda, Pregunta, TipoPregunta, TipoSegmentacion
from encuestas.services import (
    DEFAULT_ENCUESTAS_SCHEDULER_POLL_SECONDS,
    actualizar_segmentacion,
    crear_encuesta,
    get_encuestas_scheduler_poll_seconds,
    procesar_rondas_pendientes,
    publicar,
)


@pytest.fixture
def usuario_creador(django_user_model):
    return django_user_model.objects.create_user(username="creador", password="x")


def _publicar(usuario_creador, *, recurrente=False, intervalo_recurrencia_dias=None):
    encuesta = crear_encuesta(
        usuario=usuario_creador,
        titulo="Clima laboral",
        es_obligatoria=True,
        es_recurrente=recurrente,
        intervalo_recurrencia_dias=intervalo_recurrencia_dias,
        duracion_ronda_dias=7,
    )
    Pregunta.objects.create(
        encuesta=encuesta, texto="¿Todo bien?", tipo=TipoPregunta.SI_NO
    )
    actualizar_segmentacion(encuesta, tipo=TipoSegmentacion.TODOS_LOS_USUARIOS)
    ronda = publicar(encuesta, usuario=usuario_creador)
    return encuesta, ronda


@pytest.mark.django_db
def test_cierra_ronda_con_fecha_vencida(usuario_creador):
    encuesta, ronda = _publicar(usuario_creador)
    ronda.fecha_cierre_programada = timezone.now() - timedelta(minutes=1)
    ronda.save(update_fields=["fecha_cierre_programada"])

    resultado = procesar_rondas_pendientes()

    ronda.refresh_from_db()
    assert resultado["rondas_cerradas"] == 1
    assert ronda.estado == EstadoRonda.CERRADA
    assert ronda.cerrada_manualmente is False
    assert ronda.fecha_cierre_real is not None


@pytest.mark.django_db
def test_no_cierra_ronda_sin_vencer(usuario_creador):
    _, ronda = _publicar(usuario_creador)
    ronda.fecha_cierre_programada = timezone.now() + timedelta(days=1)
    ronda.save(update_fields=["fecha_cierre_programada"])

    resultado = procesar_rondas_pendientes()

    ronda.refresh_from_db()
    assert resultado["rondas_cerradas"] == 0
    assert ronda.estado == EstadoRonda.ABIERTA


@pytest.mark.django_db
def test_abre_nueva_ronda_recurrente_tras_el_intervalo(usuario_creador):
    encuesta, ronda = _publicar(
        usuario_creador, recurrente=True, intervalo_recurrencia_dias=5
    )
    # Cierra la primera manualmente y retrasa su apertura para simular que ya
    # pasó el intervalo de recurrencia.
    ronda.fecha_apertura = timezone.now() - timedelta(days=6)
    ronda.fecha_cierre_programada = timezone.now() - timedelta(days=1)
    ronda.estado = EstadoRonda.CERRADA
    ronda.fecha_cierre_real = timezone.now() - timedelta(days=1)
    ronda.save()

    resultado = procesar_rondas_pendientes()

    assert resultado["rondas_abiertas"] == 1
    assert encuesta.rondas.filter(estado=EstadoRonda.ABIERTA).count() == 1
    nueva = encuesta.rondas.get(estado=EstadoRonda.ABIERTA)
    assert nueva.numero_ronda == 2


@pytest.mark.django_db
def test_no_abre_nueva_ronda_si_no_paso_el_intervalo(usuario_creador):
    encuesta, ronda = _publicar(
        usuario_creador, recurrente=True, intervalo_recurrencia_dias=30
    )
    ronda.estado = EstadoRonda.CERRADA
    ronda.fecha_cierre_real = timezone.now()
    ronda.save()

    resultado = procesar_rondas_pendientes()

    assert resultado["rondas_abiertas"] == 0
    assert encuesta.rondas.count() == 1


@pytest.mark.django_db
def test_no_abre_nueva_ronda_para_encuesta_no_recurrente(usuario_creador):
    encuesta, ronda = _publicar(usuario_creador, recurrente=False)
    ronda.estado = EstadoRonda.CERRADA
    ronda.fecha_cierre_real = timezone.now() - timedelta(days=100)
    ronda.save()

    resultado = procesar_rondas_pendientes()

    assert resultado["rondas_abiertas"] == 0
    assert encuesta.rondas.count() == 1


@pytest.mark.django_db
def test_no_abre_nueva_ronda_si_ya_hay_una_abierta(usuario_creador):
    encuesta, ronda = _publicar(
        usuario_creador, recurrente=True, intervalo_recurrencia_dias=1
    )
    ronda.fecha_apertura = timezone.now() - timedelta(days=10)
    ronda.save(update_fields=["fecha_apertura"])

    resultado = procesar_rondas_pendientes()

    assert resultado["rondas_abiertas"] == 0
    assert encuesta.rondas.count() == 1


@pytest.mark.django_db
def test_cierra_y_abre_en_la_misma_pasada(usuario_creador):
    encuesta, ronda = _publicar(
        usuario_creador, recurrente=True, intervalo_recurrencia_dias=7
    )
    ronda.fecha_apertura = timezone.now() - timedelta(days=7)
    ronda.fecha_cierre_programada = timezone.now() - timedelta(minutes=1)
    ronda.save()

    resultado = procesar_rondas_pendientes()

    assert resultado["rondas_cerradas"] == 1
    assert resultado["rondas_abiertas"] == 1
    assert encuesta.rondas.filter(estado=EstadoRonda.ABIERTA).count() == 1


@pytest.mark.django_db
def test_management_command_once_no_bloquea(usuario_creador):
    _publicar(usuario_creador)
    call_command("process_encuestas_rondas", "--once")


def test_get_encuestas_scheduler_poll_seconds_default(monkeypatch):
    monkeypatch.delenv("ENCUESTAS_SCHEDULER_POLL_SECONDS", raising=False)
    assert (
        get_encuestas_scheduler_poll_seconds()
        == DEFAULT_ENCUESTAS_SCHEDULER_POLL_SECONDS
    )


def test_get_encuestas_scheduler_poll_seconds_desde_env(monkeypatch):
    monkeypatch.setenv("ENCUESTAS_SCHEDULER_POLL_SECONDS", "45")
    assert get_encuestas_scheduler_poll_seconds() == 45


def test_get_encuestas_scheduler_poll_seconds_invalido_usa_default(monkeypatch):
    monkeypatch.setenv("ENCUESTAS_SCHEDULER_POLL_SECONDS", "no-es-un-numero")
    assert (
        get_encuestas_scheduler_poll_seconds()
        == DEFAULT_ENCUESTAS_SCHEDULER_POLL_SECONDS
    )
