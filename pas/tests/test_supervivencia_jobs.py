"""Pruebas de regresión de la programación mensual y el avance persistente."""

from contextlib import contextmanager
from datetime import datetime, date
from threading import Barrier, Lock
from unittest.mock import Mock, patch
from zoneinfo import ZoneInfo

import pytest
import requests
from django.test import override_settings

from core.integrations.renaper import APIClient
from core.models import Municipio, Provincia
from pas.models import (
    PasControlRenaper,
    PasEstado,
    PasPersona,
    PasSupervivenciaRun,
    PasSupervivenciaBatch,
)
from pas.services import supervivencia_jobs as jobs


@contextmanager
def acquired():
    yield True


class RenaperResponse:
    """Respuesta HTTP determinista para probar consultas y renovación del token."""

    def __init__(self, payload, *, status_code=200):
        self.payload = payload
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(response=self)

    def json(self):
        return self.payload


@pytest.fixture
def personas_supervivencia(db):
    provincia = Provincia.objects.create(nombre="Provincia jobs RENAPER")
    municipio = Municipio.objects.create(
        nombre="Municipio jobs RENAPER", provincia=provincia
    )
    estado = PasEstado.objects.create(nombre="Activo jobs RENAPER")
    return [
        PasPersona.objects.create(
            id_persona=880000 + number,
            apellidos="Control",
            nombres=f"Persona {number}",
            dni=30880000 + number,
            provincia=provincia,
            municipio=municipio,
            estado=estado,
        )
        for number in range(1, 5)
    ]


@pytest.mark.parametrize(
    "day,expected",
    [
        (date(2028, 2, 28), False),
        (date(2028, 2, 29), True),
        (date(2026, 4, 30), True),
        (date(2026, 5, 30), False),
        (date(2026, 5, 31), True),
    ],
)
@override_settings(PAS_MONTHLY_ENABLED=True)
def test_fin_de_mes(day, expected):
    now = datetime.combine(
        day, datetime.min.time(), ZoneInfo("America/Argentina/Buenos_Aires")
    ).replace(hour=2)
    with (
        patch.object(jobs.timezone, "localtime", return_value=now),
        patch.object(jobs, "request_run") as request,
    ):
        jobs.schedule_monthly()
    assert request.called is expected


@pytest.mark.django_db
def test_pedido_manual_y_programado_comparten_periodo():
    first = jobs.request_run(cutoff=date(2026, 9, 30))
    second = jobs.request_run(cutoff=date(2026, 9, 30), origin="scheduled")
    assert first.pk == second.pk
    assert PasSupervivenciaRun.objects.count() == 1


def test_cliente_autentica_una_vez_para_varias_personas():
    client = APIClient(reuse_token=True)
    response = RenaperResponse({"isSuccess": True, "result": {}})
    with (
        patch.object(client, "_login", return_value="token") as login,
        patch.object(client.session, "get", return_value=response) as get,
    ):
        for number in range(20):
            client.consultar_ciudadano(str(number), "M")
    assert login.call_count == 1
    assert get.call_count == 20


def test_limitador_incluye_reintento_posterior_al_refresco_del_token():
    before_request = Mock()
    client = APIClient(reuse_token=True, before_request=before_request)
    unauthorized = RenaperResponse(
        {"isSuccess": False},
        status_code=401,
    )
    success = RenaperResponse({"isSuccess": True, "result": {}})
    with (
        patch.object(client, "_login", side_effect=["old-token", "new-token"]) as login,
        patch.object(client.session, "get", side_effect=[unauthorized, success]),
    ):
        result = client.consultar_ciudadano("30123456", "M")

    assert result["success"] is True
    assert login.call_count == 2
    assert before_request.call_count == 2


def test_limitador_espacia_el_flujo_agregado_de_solicitudes():
    now = [0.0]
    sleeps = []

    def sleep(delay):
        sleeps.append(delay)
        now[0] += delay

    limiter = jobs.AggregateRateLimiter(16, clock=lambda: now[0], sleeper=sleep)
    for _request in range(4):
        limiter.wait()

    assert sleeps == pytest.approx([1 / 16, 1 / 16, 1 / 16])


@pytest.mark.django_db(transaction=True)
@override_settings(PAS_CONCURRENCY=2, PAS_REQUESTS_PER_SECOND=16)
def test_lote_usa_un_cliente_por_hilo_y_confirma_la_ventana(
    personas_supervivencia,
):
    run = jobs.request_run(cutoff=date(2026, 9, 30))
    run.status = "running"
    run.save()
    batch = PasSupervivenciaBatch.objects.create(
        run=run,
        persona_ids=[persona.pk for persona in personas_supervivencia[:2]],
        size=2,
    )
    barrier = Barrier(2)
    seen_clients = set()
    seen_lock = Lock()

    def consult(_persona, *, client):
        with seen_lock:
            seen_clients.add(id(client))
        barrier.wait(timeout=5)
        return {"success": True, "data": {}}, "M"

    with (
        patch.object(jobs, "execution_lock", acquired),
        patch.object(jobs, "_consultar_persona", side_effect=consult),
        patch.object(jobs, "APIClient", side_effect=lambda **_kwargs: Mock()),
    ):
        jobs.process_batch(batch.pk)

    batch.refresh_from_db()
    assert len(seen_clients) == 2
    assert batch.position == 2
    assert batch.status == "completed"
    assert PasControlRenaper.objects.filter(run=run).count() == 2


@pytest.mark.django_db
@override_settings(PAS_CONCURRENCY=2, PAS_REQUESTS_PER_SECOND=16)
def test_punto_de_control_revierte_ventana_completa_ante_falla_de_escritura(
    personas_supervivencia,
):
    run = jobs.request_run(cutoff=date(2026, 9, 30))
    run.status = "running"
    run.save()
    batch = PasSupervivenciaBatch.objects.create(
        run=run,
        persona_ids=[persona.pk for persona in personas_supervivencia[:2]],
        size=2,
    )
    save_result = jobs._guardar_resultado
    saved = 0

    def fail_second_write(*args, **kwargs):
        nonlocal saved
        saved += 1
        if saved == 2:
            raise RuntimeError("caída simulada del worker")
        return save_result(*args, **kwargs)

    with (
        patch.object(jobs, "execution_lock", acquired),
        patch.object(
            jobs,
            "_consultar_persona",
            return_value=({"success": True, "data": {}}, "M"),
        ),
        patch.object(jobs, "_guardar_resultado", side_effect=fail_second_write),
        patch.object(jobs, "APIClient", side_effect=lambda **_kwargs: Mock()),
        pytest.raises(RuntimeError, match="caída simulada del worker"),
    ):
        jobs.process_batch(batch.pk)

    batch.refresh_from_db()
    assert batch.position == 0
    assert not PasControlRenaper.objects.filter(run=run).exists()


@pytest.mark.django_db
@override_settings(
    PAS_CONCURRENCY=2,
    PAS_REQUESTS_PER_SECOND=16,
    PAS_CIRCUIT_BREAKER_TIMEOUTS=8,
)
def test_ventana_sin_exito_pausa_sin_encolar_mas_personas(
    personas_supervivencia,
):
    run = jobs.request_run(cutoff=date(2026, 9, 30))
    run.status = "running"
    run.save()
    batch = PasSupervivenciaBatch.objects.create(
        run=run,
        persona_ids=[persona.pk for persona in personas_supervivencia],
        size=4,
    )
    timeout = ({"success": False, "error_type": "timeout"}, "M")
    with (
        patch.object(jobs, "execution_lock", acquired),
        patch.object(jobs, "_consultar_persona", return_value=timeout) as consult,
        patch.object(jobs, "APIClient", side_effect=lambda **_kwargs: Mock()),
    ):
        jobs.process_batch(batch.pk)

    batch.refresh_from_db()
    run.refresh_from_db()
    assert consult.call_count == 2
    assert batch.position == 0
    assert run.status == "paused"
    assert not PasControlRenaper.objects.filter(run=run).exists()


@pytest.mark.django_db
@override_settings(
    PAS_CONCURRENCY=2,
    PAS_REQUESTS_PER_SECOND=16,
    PAS_CIRCUIT_BREAKER_TIMEOUTS=99,
)
def test_falla_transitoria_reintenta_tres_veces_y_confirma(
    personas_supervivencia,
):
    first, second = personas_supervivencia[:2]
    run = jobs.request_run(cutoff=date(2026, 9, 30))
    run.status = "running"
    run.save()
    batch = PasSupervivenciaBatch.objects.create(
        run=run, persona_ids=[first.pk, second.pk], size=2
    )
    calls = {first.pk: 0, second.pk: 0}

    def consult(persona, *, client):
        del client
        calls[persona.pk] += 1
        if persona.pk == first.pk:
            return {"success": True, "data": {}}, "M"
        return {"success": False, "error_type": "timeout"}, "M"

    with (
        patch.object(jobs, "execution_lock", acquired),
        patch.object(jobs, "_consultar_persona", side_effect=consult),
        patch.object(jobs, "APIClient", side_effect=lambda **_kwargs: Mock()),
    ):
        jobs.process_batch(batch.pk)

    batch.refresh_from_db()
    assert calls == {first.pk: 1, second.pk: 4}
    assert batch.position == 2
    assert batch.counts == {"vigente": 1, "error": 1}


@pytest.mark.django_db
def test_reentrega_conserva_punto_de_control_para_persona_eliminada():
    run = jobs.request_run(cutoff=date(2026, 9, 30))
    run.status = "running"
    run.save()
    batch = PasSupervivenciaBatch.objects.create(
        run=run, persona_ids=[999999999], size=1
    )
    with patch.object(jobs, "execution_lock", acquired):
        jobs.process_batch(batch.pk)
        jobs.process_batch(batch.pk)
    batch.refresh_from_db()
    assert batch.position == 1
    assert batch.counts == {"deleted": 1}


def test_bloqueo_ocupado_no_consulta_el_padron():
    @contextmanager
    def busy():
        yield False

    with (
        patch.object(jobs, "execution_lock", busy),
        patch.object(jobs.PasSupervivenciaBatch.objects, "select_related") as query,
    ):
        jobs.process_batch(123)
        jobs.reconcile_jobs()
    query.assert_not_called()


@pytest.mark.django_db
@override_settings(PAS_BATCH_SIZE=2000)
def test_fija_250000_ids_en_125_lotes_de_2000():
    run = jobs.request_run(cutoff=date(2026, 9, 30))
    with patch.object(jobs.PasPersona.objects, "order_by") as roster:
        roster.return_value.values_list.return_value.iterator.return_value = iter(
            range(1, 250001)
        )
        jobs._prepare(run)
    assert run.batches.count() == 125
    assert run.batches.first().size == 2000
    assert run.batches.last().persona_ids[-1] == 250000
    assert jobs.run_summary()["total"] == 250000


@pytest.mark.django_db
def test_publicacion_perdida_permanece_recuperable():
    run = jobs.request_run(cutoff=date(2026, 9, 30))
    run.status = "running"
    run.active_slot = 1
    run.save()
    batch = PasSupervivenciaBatch.objects.create(run=run, persona_ids=[1], size=1)
    with (
        patch.object(jobs, "execution_lock", acquired),
        patch.object(jobs.current_app, "send_task", side_effect=ConnectionError),
    ):
        with pytest.raises(ConnectionError):
            jobs.reconcile_jobs()
    batch.refresh_from_db()
    assert batch.dispatched_at is None
    with (
        patch.object(jobs, "execution_lock", acquired),
        patch.object(jobs.current_app, "send_task") as publish,
    ):
        jobs.reconcile_jobs()
    publish.assert_called_once()
