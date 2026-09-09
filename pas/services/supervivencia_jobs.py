"""Trabajo persistente de PAS con bloqueo de sesión MySQL durante llamadas externas.

Se ejecuta un único lote global. Escalar requiere revisar explícitamente la
cuota RENAPER; el bloqueo protege ejecuciones manuales, programadas y reentregadas.
"""

import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import timedelta

from celery import current_app

from django.conf import settings
from django.db import connection, transaction
from django.db.models import Max
from django.utils import timezone

from core.integrations.renaper import APIClient
from pas.models import PasPersona, PasSupervivenciaRun, PasSupervivenciaBatch
from pas.services.supervivencia_service import _consultar_persona, _guardar_resultado

logger = logging.getLogger("django")
TRANSIENT_ERRORS = {"timeout", "remote_error"}
SYSTEM_ERRORS = TRANSIENT_ERRORS | {"auth_error", "invalid_response"}
MAX_TRANSIENT_RETRIES = 3


class AggregateRateLimiter:
    """Espacia globalmente las solicitudes sin depender de la cantidad de hilos."""

    def __init__(self, rate, *, clock=time.monotonic, sleeper=time.sleep):
        self.interval = 1 / rate
        self.clock = clock
        self.sleeper = sleeper
        self.lock = threading.Lock()
        self.next_slot = 0.0

    def wait(self):
        with self.lock:
            now = self.clock()
            slot = max(now, self.next_slot)
            self.next_slot = slot + self.interval
        delay = slot - now
        if delay > 0:
            self.sleeper(delay)


class _ThreadClients:
    """Crea una sesión y un token RENAPER independientes por hilo ejecutor."""

    def __init__(self, limiter):
        self.limiter = limiter
        self.local = threading.local()
        self.clients = []
        self.lock = threading.Lock()

    def get(self):
        client = getattr(self.local, "client", None)
        if client is None:
            client = APIClient(reuse_token=True, before_request=self.limiter.wait)
            self.local.client = client
            with self.lock:
                self.clients.append(client)
        return client

    def close(self):
        for client in self.clients:
            client.session.close()


@contextmanager
def execution_lock():
    """Bloqueo de conexión: un worker caído lo libera sin dejar una reserva vencida."""
    if connection.vendor != "mysql":
        raise RuntimeError("La ejecución en segundo plano de PAS requiere MySQL")
    with connection.cursor() as cursor:
        cursor.execute("SELECT GET_LOCK(%s, 0)", ["pas_supervivencia"])
        acquired = cursor.fetchone()[0] == 1
    try:
        yield acquired
    finally:
        if acquired:
            with connection.cursor() as cursor:
                cursor.execute("SELECT RELEASE_LOCK(%s)", ["pas_supervivencia"])


def request_run(*, actor=None, cutoff=None, origin="manual"):
    """La web registra el pedido mínimo; Beat reconcilia fallas de publicación."""
    cutoff = cutoff or timezone.localdate()
    with transaction.atomic():
        run, _ = PasSupervivenciaRun.objects.get_or_create(
            period=cutoff.replace(day=1),
            defaults={"cutoff": cutoff, "requested_by": actor, "origin": origin},
        )
    return run


def schedule_monthly():
    now = timezone.localtime()
    if not settings.PAS_MONTHLY_ENABLED or now.hour != 2:
        return
    if (now.date() + timedelta(days=1)).month != now.month:
        request_run(cutoff=now.date(), origin="scheduled")


def _prepare(run):
    """Fija el padrón en una transacción; la web nunca carga la nómina completa."""
    with transaction.atomic():
        run.batches.all().delete()
        run.active_slot = 1
        run.status = "running"
        run.save(update_fields=["active_slot", "status"])
        ids = []
        for persona_id in (
            PasPersona.objects.order_by("pk")
            .values_list("pk", flat=True)
            .iterator(chunk_size=2000)
        ):
            ids.append(persona_id)
            if len(ids) == settings.PAS_BATCH_SIZE:
                PasSupervivenciaBatch.objects.create(
                    run=run, persona_ids=ids, size=len(ids)
                )
                ids = []
        if ids:
            PasSupervivenciaBatch.objects.create(
                run=run, persona_ids=ids, size=len(ids)
            )


def reconcile_jobs():
    """Publica un solo lote y recupera entregas perdidas tras una espera acotada."""
    with execution_lock() as acquired:
        if not acquired:
            return
        run = PasSupervivenciaRun.objects.filter(active_slot=1).first()
        if run is None:
            run = (
                PasSupervivenciaRun.objects.filter(status="pending")
                .order_by("pk")
                .first()
            )
            if run is None:
                return
            _prepare(run)
        if run.status == "paused":
            return
        batch = run.batches.exclude(status="completed").order_by("pk").first()
        if batch is None:
            has_errors = any(
                b.counts.get("error", 0) for b in run.batches.defer("persona_ids")
            )
            run.status = "completed_with_errors" if has_errors else "completed"
            run.finished_at = timezone.now()
            run.active_slot = None
            run.save()
            return
        # Tener el bloqueo de sesión prueba que no hay otro lote ejecutándose.
        if batch.dispatched_at and batch.dispatched_at > timezone.now() - timedelta(
            minutes=5 * 2 ** max(0, batch.attempts - 1)
        ):
            return
        current_app.send_task("pas.tasks.run_batch", args=[batch.pk], queue="pas")
        batch.dispatched_at = timezone.now()
        batch.save(update_fields=["dispatched_at"])


def process_batch(batch_id):
    with execution_lock() as acquired:
        if not acquired:
            return
        batch = PasSupervivenciaBatch.objects.select_related("run").get(pk=batch_id)
        if batch.status == "completed" or batch.run.status != "running":
            return
        concurrency = settings.PAS_CONCURRENCY
        limiter = AggregateRateLimiter(settings.PAS_REQUESTS_PER_SECOND)
        clients = _ThreadClients(limiter)
        started = time.monotonic()
        try:
            with ThreadPoolExecutor(max_workers=concurrency) as executor:
                _process_windows(batch, executor, clients, started, concurrency)
        finally:
            clients.close()


def _process_windows(batch, executor, clients, started, concurrency):
    consecutive_timeouts = 0
    while batch.position < len(batch.persona_ids):
        if time.monotonic() - started >= settings.PAS_BATCH_SECONDS:
            break
        window_ids = batch.persona_ids[batch.position : batch.position + concurrency]
        paused, consecutive_timeouts = _process_window(
            batch, window_ids, executor, clients, consecutive_timeouts
        )
        if paused:
            return


def _process_window(batch, window_ids, executor, clients, consecutive_timeouts):
    personas = PasPersona.objects.in_bulk(window_ids)
    outcomes = {persona_id: ({}, "") for persona_id in window_ids}
    pending = [
        personas[persona_id] for persona_id in window_ids if persona_id in personas
    ]

    for attempt in range(MAX_TRANSIENT_RETRIES + 1):
        if not pending:
            break
        round_outcomes = list(
            executor.map(
                lambda persona: _consultar_persona(persona, client=clients.get()),
                pending,
            )
        )
        for persona, outcome in zip(pending, round_outcomes):
            outcomes[persona.pk] = outcome

        errors = [result.get("error_type") for result, _sexo in round_outcomes]
        for error in errors:
            consecutive_timeouts = consecutive_timeouts + 1 if error == "timeout" else 0
        if "auth_error" in errors:
            _pause_batch(batch, "auth_error")
            return True, consecutive_timeouts
        zero_success = (
            attempt == 0
            and len(round_outcomes) == len(personas)
            and bool(errors)
            and all(error in SYSTEM_ERRORS for error in errors)
        )
        if (
            consecutive_timeouts >= settings.PAS_CIRCUIT_BREAKER_TIMEOUTS
            or zero_success
        ):
            _pause_batch(batch, "circuit_breaker")
            return True, consecutive_timeouts
        pending = [
            persona
            for persona, (result, _sexo) in zip(pending, round_outcomes)
            if result.get("error_type") in TRANSIENT_ERRORS
        ]

    _checkpoint_window(batch, window_ids, personas, outcomes)
    return False, consecutive_timeouts


def _pause_batch(batch, reason):
    """Pausa solo después de que el ejecutor haya drenado la ventana activa."""
    now = timezone.now()
    with transaction.atomic():
        batch.run.status = "paused"
        batch.run.save(update_fields=["status"])
        batch.heartbeat = now
        batch.attempts = batch.attempts + 1
        batch.dispatched_at = None
        batch.save(update_fields=["heartbeat", "attempts", "dispatched_at"])
    logger.error(
        "pas.renaper.paused",
        extra={"data": {"run": batch.run_id, "batch": batch.pk, "reason": reason}},
    )


def _checkpoint_window(batch, window_ids, personas, outcomes):
    """Persiste la ventana drenada y avanza su punto de control una sola vez."""
    counts = dict(batch.counts)
    with transaction.atomic():
        for persona_id in window_ids:
            persona = personas.get(persona_id)
            if persona is None:
                key = "deleted"
            else:
                result, sexo = outcomes[persona_id]
                control, incompatibilidad = _guardar_resultado(
                    persona, batch.run.cutoff, result, sexo
                )
                control.run = batch.run
                control.save(update_fields=["run"])
                if incompatibilidad is not None:
                    incompatibilidad.run = batch.run
                    incompatibilidad.save(update_fields=["run"])
                key = control.resultado
            counts[key] = counts.get(key, 0) + 1
        batch.counts = counts
        batch.position += len(window_ids)
        batch.attempts = 0
        batch.heartbeat = timezone.now()
        batch.status = (
            "completed" if batch.position == len(batch.persona_ids) else "pending"
        )
        batch.dispatched_at = None
        batch.save()


def run_summary():
    run = PasSupervivenciaRun.objects.order_by("-pk").first()
    if run is None:
        return None
    batches = list(run.batches.defer("persona_ids"))
    return {
        "id": run.pk,
        "status": {
            "pending": "Pendiente",
            "running": "En proceso",
            "paused": "Requiere intervención",
            "completed": "Completada",
            "completed_with_errors": "Completada con errores",
        }.get(run.status, run.status),
        "cutoff": run.cutoff,
        "total": sum(b.size for b in batches),
        "processed": sum(b.position for b in batches),
        "heartbeat": run.batches.aggregate(value=Max("heartbeat"))["value"],
    }
