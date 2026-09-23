from __future__ import annotations

import logging
import os
import threading
import time
import uuid
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import (
    DatabaseError,
    IntegrityError,
    OperationalError,
    close_old_connections,
    models,
    transaction,
)
from django.db.models.functions import Coalesce
from django.http import Http404
from django.utils import timezone

from ciudadanos.models import Ciudadano, CiudadanosImportJob, CiudadanosImportJobRow
from ciudadanos.services_importacion_masiva import (
    _get_existing_estandar_by_dni,
    build_ciudadanos_import_error_message,
    load_ciudadanos_import_rows,
    process_ciudadanos_import_row,
    validate_ciudadanos_import_workbook,
)
from core.integrations.renaper import APIClient

logger = logging.getLogger("django")
DEFAULT_CIUDADANOS_IMPORT_JOB_POLL_SECONDS = 5
DEFAULT_CIUDADANOS_IMPORT_JOB_STALE_SECONDS = 900
DEFAULT_CIUDADANOS_IMPORT_RENAPER_SLEEP_SECONDS = 0.0
DEFAULT_CIUDADANOS_IMPORT_RENAPER_PARALLELISM = 4
DEFAULT_CIUDADANOS_IMPORT_JOB_SLICE_SECONDS = 300


class LostImportLease(RuntimeError):
    """Otro worker recuperó el lote; este proceso no debe escribir más filas."""


def _setting_or_env(name: str):
    value = getattr(settings, name, None)
    if value is not None:
        return value
    return os.getenv(name, "")


def _safe_positive_int(value, default: int) -> int:
    try:
        parsed = int(str(value).strip())
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def _safe_non_negative_float(value, default: float) -> float:
    try:
        parsed = float(str(value).strip())
    except (TypeError, ValueError):
        return default
    return parsed if parsed >= 0 else default


def get_ciudadanos_import_job_poll_seconds() -> int:
    return _safe_positive_int(
        _setting_or_env("CIUDADANOS_IMPORT_JOB_POLL_SECONDS"),
        DEFAULT_CIUDADANOS_IMPORT_JOB_POLL_SECONDS,
    )


def get_ciudadanos_import_job_stale_seconds() -> int:
    return _safe_positive_int(
        _setting_or_env("CIUDADANOS_IMPORT_JOB_STALE_SECONDS"),
        DEFAULT_CIUDADANOS_IMPORT_JOB_STALE_SECONDS,
    )


def get_ciudadanos_import_renaper_sleep_seconds() -> float:
    return _safe_non_negative_float(
        _setting_or_env("CIUDADANOS_IMPORT_RENAPER_SLEEP_SECONDS"),
        DEFAULT_CIUDADANOS_IMPORT_RENAPER_SLEEP_SECONDS,
    )


def get_ciudadanos_import_renaper_parallelism() -> int:
    default = (
        1 if settings.RUNNING_TESTS else DEFAULT_CIUDADANOS_IMPORT_RENAPER_PARALLELISM
    )
    return _safe_positive_int(
        _setting_or_env("CIUDADANOS_IMPORT_RENAPER_PARALLELISM"), default
    )


def get_ciudadanos_import_job_slice_seconds() -> int:
    return _safe_positive_int(
        _setting_or_env("CIUDADANOS_IMPORT_JOB_SLICE_SECONDS"),
        DEFAULT_CIUDADANOS_IMPORT_JOB_SLICE_SECONDS,
    )


def create_ciudadanos_import_job(*, uploaded_file, requested_by):
    validate_ciudadanos_import_workbook(uploaded_file)
    job = CiudadanosImportJob(
        requested_by=requested_by,
        original_filename=getattr(uploaded_file, "name", "ciudadanos.xlsx"),
    )
    uploaded_file.seek(0)
    job.archivo.save(job.original_filename, uploaded_file, save=False)
    job.save()
    return job


def get_ciudadanos_import_job_queryset():
    return CiudadanosImportJob.objects.select_related("requested_by").order_by(
        "-requested_at", "-id"
    )


def get_recent_ciudadanos_import_jobs(limit: int = 10):
    return list(get_ciudadanos_import_job_queryset()[:limit])


def get_ciudadanos_import_job_or_404(*, job_id: int):
    job = get_ciudadanos_import_job_queryset().filter(pk=job_id).first()
    if not job:
        raise Http404("No existe el lote solicitado.")
    return job


def can_resume_ciudadanos_import_job(job: CiudadanosImportJob) -> bool:
    return job.status == CiudadanosImportJob.Status.FAILED


def request_resume_ciudadanos_import_job(
    *, job: CiudadanosImportJob
) -> CiudadanosImportJob:
    if not can_resume_ciudadanos_import_job(job):
        raise ValidationError("Solo se pueden reanudar lotes fallidos.")

    job.status = CiudadanosImportJob.Status.PENDING
    job.last_error_message = ""
    job.last_error_type = ""
    job.last_error_at = None
    job.finished_at = None
    job.resume_count += 1
    job.lease_token = None
    job.last_activity_at = timezone.now()
    job.save(
        update_fields=[
            "status",
            "last_error_message",
            "last_error_type",
            "last_error_at",
            "finished_at",
            "resume_count",
            "lease_token",
            "last_activity_at",
        ]
    )
    return job


def mark_stale_ciudadanos_import_jobs_as_failed() -> int:
    stale_threshold = timezone.now() - timedelta(
        seconds=get_ciudadanos_import_job_stale_seconds()
    )
    stale_jobs = CiudadanosImportJob.objects.filter(
        status=CiudadanosImportJob.Status.PROCESSING,
    ).filter(
        models.Q(last_activity_at__isnull=True)
        | models.Q(last_activity_at__lt=stale_threshold)
    )
    updated_count = 0
    for job_id, lease_token in list(stale_jobs.values_list("pk", "lease_token")):
        updated_count += (
            CiudadanosImportJob.objects.filter(
                pk=job_id,
                status=CiudadanosImportJob.Status.PROCESSING,
                lease_token=lease_token,
            )
            .filter(
                models.Q(last_activity_at__isnull=True)
                | models.Q(last_activity_at__lt=stale_threshold)
            )
            .update(
                status=CiudadanosImportJob.Status.PENDING,
                lease_token=None,
                resume_count=models.F("resume_count") + 1,
                last_activity_at=timezone.now(),
            )
        )
    return updated_count


def claim_next_ciudadanos_import_job() -> CiudadanosImportJob | None:
    candidate_ids = list(
        CiudadanosImportJob.objects.filter(status=CiudadanosImportJob.Status.PENDING)
        .annotate(queue_time=Coalesce("last_activity_at", "requested_at"))
        .order_by("queue_time", "id")
        .values_list("id", flat=True)[:20]
    )
    now = timezone.now()
    for job_id in candidate_ids:
        lease_token = uuid.uuid4()
        updated = CiudadanosImportJob.objects.filter(
            pk=job_id,
            status=CiudadanosImportJob.Status.PENDING,
        ).update(
            status=CiudadanosImportJob.Status.PROCESSING,
            finished_at=None,
            last_activity_at=now,
            lease_token=lease_token,
        )
        if not updated:
            continue

        job = CiudadanosImportJob.objects.get(pk=job_id)
        if not job.started_at:
            job.started_at = now
            job.save(update_fields=["started_at"])
        return job
    return None


def _lock_owned_job(job: CiudadanosImportJob) -> None:
    if job.lease_token is None:
        raise LostImportLease(f"El worker no reclamó el lote #{job.pk}.")
    current = CiudadanosImportJob.objects.select_for_update().get(pk=job.pk)
    if (
        current.status != CiudadanosImportJob.Status.PROCESSING
        or current.lease_token != job.lease_token
    ):
        raise LostImportLease(f"El worker perdió el lote #{job.pk}.")


def _save_owned_job(job: CiudadanosImportJob, update_fields: list[str]) -> None:
    if job.lease_token is None:
        raise LostImportLease(f"El worker no reclamó el lote #{job.pk}.")
    updated = CiudadanosImportJob.objects.filter(
        pk=job.pk,
        status=CiudadanosImportJob.Status.PROCESSING,
        lease_token=job.lease_token,
    ).update(**{field: getattr(job, field) for field in update_fields})
    if not updated:
        raise LostImportLease(f"El worker perdió el lote #{job.pk}.")


def _ensure_job_claimed(job: CiudadanosImportJob) -> None:
    """Permite el procesamiento directo sólo si el lote sigue pendiente."""
    if job.lease_token is not None:
        return
    token = uuid.uuid4()
    updated = CiudadanosImportJob.objects.filter(
        pk=job.pk,
        status=CiudadanosImportJob.Status.PENDING,
        lease_token__isnull=True,
    ).update(
        status=CiudadanosImportJob.Status.PROCESSING,
        lease_token=token,
        last_activity_at=timezone.now(),
    )
    if not updated:
        raise LostImportLease(f"El worker no pudo reclamar el lote #{job.pk}.")
    job.lease_token = token
    job.status = CiudadanosImportJob.Status.PROCESSING


def _recalculate_job_counters(job: CiudadanosImportJob) -> None:
    rows = job.rows.all()
    created_rows = rows.filter(status=CiudadanosImportJobRow.Status.CREATED).count()
    existing_rows = rows.filter(status=CiudadanosImportJobRow.Status.EXISTING).count()
    failed_rows = rows.filter(status=CiudadanosImportJobRow.Status.FAILED).count()
    processed_rows = created_rows + existing_rows + failed_rows
    job.created_rows = created_rows
    job.existing_rows = existing_rows
    job.failed_rows = failed_rows
    job.processed_rows = processed_rows
    job.pending_rows = max(job.total_rows - processed_rows, 0)


def _apply_row_counter_transition(job, old_status: str, new_status: str) -> None:
    counter_fields = {
        CiudadanosImportJobRow.Status.CREATED: "created_rows",
        CiudadanosImportJobRow.Status.EXISTING: "existing_rows",
        CiudadanosImportJobRow.Status.FAILED: "failed_rows",
    }
    if old_status == new_status:
        return
    if old_status in counter_fields:
        field = counter_fields[old_status]
        setattr(job, field, getattr(job, field) - 1)
        job.processed_rows -= 1
    if new_status in counter_fields:
        field = counter_fields[new_status]
        setattr(job, field, getattr(job, field) + 1)
        job.processed_rows += 1
    job.pending_rows = max(job.total_rows - job.processed_rows, 0)


def _sync_job_total_rows(*, job: CiudadanosImportJob, total_rows: int) -> None:
    if job.total_rows == total_rows and job.pending_rows == max(
        total_rows - job.processed_rows,
        0,
    ):
        return
    job.total_rows = total_rows
    _recalculate_job_counters(job)
    _save_owned_job(
        job,
        [
            "total_rows",
            "processed_rows",
            "created_rows",
            "existing_rows",
            "failed_rows",
            "pending_rows",
        ],
    )


def _load_job_rows(job: CiudadanosImportJob):
    try:
        job.archivo.open("rb")
        return load_ciudadanos_import_rows(job.archivo)
    except ValidationError as exc:
        _record_job_level_failure(
            job=job,
            message=build_ciudadanos_import_error_message(exc),
            error_type="invalid_file",
        )
    except Exception as exc:
        logger.exception(
            "Fallo leyendo archivo de lote de importacion de ciudadanos. job_id=%s",
            job.id,
        )
        _record_job_level_failure(
            job=job,
            message=build_ciudadanos_import_error_message(exc),
            error_type="unexpected_error",
        )
    finally:
        try:
            job.archivo.close()
        except Exception:
            pass
    return None


def _record_job_level_failure(
    *,
    job: CiudadanosImportJob,
    message: str,
    error_type: str,
) -> CiudadanosImportJob:
    now = timezone.now()
    job.status = CiudadanosImportJob.Status.FAILED
    job.last_error_message = message
    job.last_error_type = error_type
    job.last_error_at = now
    job.finished_at = now
    job.last_activity_at = now
    _save_owned_job(
        job,
        [
            "status",
            "last_error_message",
            "last_error_type",
            "last_error_at",
            "finished_at",
            "last_activity_at",
        ],
    )
    return job


def _ensure_job_processing(job: CiudadanosImportJob) -> None:
    now = timezone.now()
    update_fields = ["status", "finished_at", "last_activity_at"]
    job.status = CiudadanosImportJob.Status.PROCESSING
    job.finished_at = None
    job.last_activity_at = now
    if not job.started_at:
        job.started_at = now
        update_fields.append("started_at")
    _save_owned_job(job, update_fields)


def _build_row_log_defaults(row) -> dict[str, object]:
    return {
        "documento_raw": row.documento_raw,
        "dni": row.dni,
        "cuil": row.cuil,
        "sexo": row.sexo,
        "status": CiudadanosImportJobRow.Status.PENDING,
        "mensaje": "",
        "error_type": "",
        "attempts": 0,
    }


@transaction.atomic
def _get_job_row_log(*, job: CiudadanosImportJob, row):
    _lock_owned_job(job)
    row_log, _ = CiudadanosImportJobRow.objects.get_or_create(
        job=job,
        fila=row.fila,
        defaults=_build_row_log_defaults(row),
    )
    return row_log


def _start_job_row_attempt(*, job: CiudadanosImportJob, row_index: int, row) -> None:
    now = timezone.now()
    job.status = CiudadanosImportJob.Status.PROCESSING
    job.next_row_index = row_index
    job.last_attempted_row = row.fila
    job.last_attempted_documento = row.dni or row.documento_raw
    job.last_activity_at = now
    _save_owned_job(
        job,
        [
            "status",
            "next_row_index",
            "last_attempted_row",
            "last_attempted_documento",
            "last_activity_at",
        ],
    )


def _apply_row_base_data(row_log: CiudadanosImportJobRow, row) -> None:
    row_log.documento_raw = row.documento_raw
    row_log.dni = row.dni
    row_log.cuil = row.cuil
    row_log.sexo = row.sexo


@transaction.atomic
def _save_row_pending_after_systemic_error(
    *,
    job: CiudadanosImportJob,
    row_log: CiudadanosImportJobRow,
    row,
    result: dict[str, object],
) -> CiudadanosImportJob:
    _lock_owned_job(job)
    _apply_row_base_data(row_log, row)
    row_log.status = CiudadanosImportJobRow.Status.PENDING
    row_log.ciudadano = None
    row_log.mensaje = str(result["mensaje"])
    row_log.error_type = str(result["error_type"])
    row_log.sexos_intentados = str(result.get("sexos_intentados") or "")
    row_log.attempts += 1
    row_log.processed_at = None
    row_log.save()

    now = timezone.now()
    _recalculate_job_counters(job)
    job.status = CiudadanosImportJob.Status.FAILED
    job.last_error_message = row_log.mensaje
    job.last_error_type = row_log.error_type
    job.last_error_at = now
    job.finished_at = now
    job.last_activity_at = now
    _save_owned_job(
        job,
        [
            "processed_rows",
            "created_rows",
            "existing_rows",
            "failed_rows",
            "pending_rows",
            "status",
            "last_error_message",
            "last_error_type",
            "last_error_at",
            "finished_at",
            "last_activity_at",
        ],
    )
    return job


def _map_result_status(result_status: str) -> str:
    return {
        "created": CiudadanosImportJobRow.Status.CREATED,
        "existing": CiudadanosImportJobRow.Status.EXISTING,
        "failed": CiudadanosImportJobRow.Status.FAILED,
    }[result_status]


def _save_row_processed(
    *,
    job: CiudadanosImportJob,
    row_log: CiudadanosImportJobRow,
    row,
    result: dict[str, object],
    next_row_index: int,
) -> CiudadanosImportJob:
    with transaction.atomic():
        _lock_owned_job(job)
        old_status = row_log.status
        if result["status"] == "ready_to_create":
            result = dict(result)
            result["ciudadano"] = Ciudadano.objects.create(**result["ciudadano_data"])
            result["status"] = "created"

        _apply_row_base_data(row_log, row)
        row_log.status = _map_result_status(str(result["status"]))
        row_log.ciudadano = result.get("ciudadano")
        row_log.mensaje = str(result["mensaje"])
        row_log.error_type = str(result.get("error_type") or "")
        row_log.sexos_intentados = str(result.get("sexos_intentados") or "")
        row_log.attempts += 1
        row_log.processed_at = timezone.now()
        row_log.save()

        now = timezone.now()
        _apply_row_counter_transition(job, old_status, row_log.status)
        job.next_row_index = next_row_index
        job.last_activity_at = now
        update_fields = [
            "processed_rows",
            "created_rows",
            "existing_rows",
            "failed_rows",
            "pending_rows",
            "next_row_index",
            "last_activity_at",
        ]
        if row_log.status in (
            CiudadanosImportJobRow.Status.CREATED,
            CiudadanosImportJobRow.Status.EXISTING,
        ):
            job.last_successful_row = row.fila
            job.last_successful_documento = row.dni or row.documento_raw
            update_fields.extend(["last_successful_row", "last_successful_documento"])
        _save_owned_job(job, update_fields)
    return job


@transaction.atomic
def _mark_job_completed(job: CiudadanosImportJob) -> CiudadanosImportJob:
    _lock_owned_job(job)
    now = timezone.now()
    _recalculate_job_counters(job)
    job.status = (
        CiudadanosImportJob.Status.COMPLETED
        if job.failed_rows == 0
        else CiudadanosImportJob.Status.COMPLETED_WITH_ERRORS
    )
    job.pending_rows = 0
    job.finished_at = now
    job.last_activity_at = now
    job.last_error_message = ""
    job.last_error_type = ""
    job.last_error_at = None
    _save_owned_job(
        job,
        [
            "processed_rows",
            "created_rows",
            "existing_rows",
            "failed_rows",
            "pending_rows",
            "status",
            "finished_at",
            "last_activity_at",
            "last_error_message",
            "last_error_type",
            "last_error_at",
        ],
    )
    return job


@transaction.atomic
def _yield_job_to_queue(job: CiudadanosImportJob) -> None:
    _lock_owned_job(job)
    now = timezone.now()
    updated = CiudadanosImportJob.objects.filter(
        pk=job.pk,
        status=CiudadanosImportJob.Status.PROCESSING,
        lease_token=job.lease_token,
    ).update(
        status=CiudadanosImportJob.Status.PENDING,
        lease_token=None,
        last_activity_at=now,
    )
    if not updated:
        raise LostImportLease(f"El worker perdió el lote #{job.pk}.")
    job.status = CiudadanosImportJob.Status.PENDING
    job.lease_token = None
    job.last_activity_at = now


def _iter_prepared_rows(rows, *, start: int, requested_by, parallelism: int):
    """Solapa consultas RENAPER; el worker principal persiste en orden."""
    if parallelism == 1:
        client = APIClient(reuse_token=True)
        try:
            for index in range(start, len(rows)):
                row = rows[index]
                yield index, row, lambda row=row: process_ciudadanos_import_row(
                    row=row, requested_by=requested_by, client=client
                )
        finally:
            client.session.close()
        return

    thread_state = threading.local()
    clients = []
    clients_lock = threading.Lock()

    def prepare(row):
        close_old_connections()
        client = getattr(thread_state, "client", None)
        if client is None:
            client = APIClient(reuse_token=True)
            thread_state.client = client
            with clients_lock:
                clients.append(client)
        try:
            return process_ciudadanos_import_row(
                row=row, requested_by=requested_by, client=client
            )
        finally:
            close_old_connections()

    try:
        with ThreadPoolExecutor(max_workers=parallelism) as executor:
            pending = deque()
            next_index = start

            def submit_next():
                nonlocal next_index
                if next_index >= len(rows):
                    return
                row = rows[next_index]
                pending.append((next_index, row, executor.submit(prepare, row)))
                next_index += 1

            for _ in range(parallelism * 2):
                submit_next()
            while pending:
                index, row, future = pending.popleft()
                yield index, row, future.result
                submit_next()
    finally:
        for client in clients:
            client.session.close()


def process_ciudadanos_import_job(
    job: CiudadanosImportJob,
) -> CiudadanosImportJob:
    if job.status in (
        CiudadanosImportJob.Status.COMPLETED,
        CiudadanosImportJob.Status.COMPLETED_WITH_ERRORS,
    ):
        return job
    _ensure_job_claimed(job)
    _ensure_job_processing(job)
    rows = _load_job_rows(job)
    if rows is None:
        return job

    total_rows = len(rows)
    _sync_job_total_rows(job=job, total_rows=total_rows)
    if job.next_row_index >= total_rows:
        return _mark_job_completed(job)

    renaper_sleep_seconds = get_ciudadanos_import_renaper_sleep_seconds()
    slice_seconds = get_ciudadanos_import_job_slice_seconds()
    slice_started_at = time.monotonic()
    prepared_rows = _iter_prepared_rows(
        rows,
        start=job.next_row_index,
        requested_by=job.requested_by,
        parallelism=get_ciudadanos_import_renaper_parallelism(),
    )
    try:
        for row_index, row, prepare in prepared_rows:
            close_old_connections()
            _start_job_row_attempt(job=job, row_index=row_index, row=row)
            row_log = _get_job_row_log(job=job, row=row)

            try:
                result = prepare()
            except DatabaseError:
                raise
            except Exception as exc:
                logger.exception(
                    (
                        "Fallo inesperado procesando lote de ciudadanos. "
                        "job_id=%s fila=%s documento=%s"
                    ),
                    job.id,
                    row.fila,
                    row.documento_raw,
                )
                error_detail = str(exc).strip()
                message = "Ocurrio un error inesperado al procesar la fila."
                if error_detail:
                    message = f"{message} Detalle: {error_detail}"
                result = {
                    "status": "failed",
                    "mensaje": message,
                    "error_type": "unexpected_row_error",
                    "sexos_intentados": "",
                    "ciudadano": None,
                    "systemic": False,
                    "contacted_renaper": False,
                }

            close_old_connections()
            if result.get("systemic"):
                return _save_row_pending_after_systemic_error(
                    job=job,
                    row_log=row_log,
                    row=row,
                    result=result,
                )

            try:
                job = _save_row_processed(
                    job=job,
                    row_log=row_log,
                    row=row,
                    result=result,
                    next_row_index=row_index + 1,
                )
            except IntegrityError:
                if result["status"] != "ready_to_create":
                    raise
                existing = _get_existing_estandar_by_dni(row.dni)
                if existing is None:
                    raise
                # La transacción se revirtió, pero las instancias en memoria no.
                row_log.refresh_from_db()
                job.refresh_from_db()
                result = {
                    **result,
                    "status": "existing",
                    "ciudadano": existing,
                    "mensaje": "Ya existe un ciudadano estandar para el DNI informado.",
                }
                job = _save_row_processed(
                    job=job,
                    row_log=row_log,
                    row=row,
                    result=result,
                    next_row_index=row_index + 1,
                )
            if (
                result.get("contacted_renaper")
                and renaper_sleep_seconds > 0
                and row_index + 1 < total_rows
            ):
                time.sleep(renaper_sleep_seconds)

            if (
                row_index + 1 < total_rows
                and time.monotonic() - slice_started_at >= slice_seconds
            ):
                if (
                    CiudadanosImportJob.objects.filter(
                        status=CiudadanosImportJob.Status.PENDING
                    )
                    .exclude(pk=job.pk)
                    .exists()
                ):
                    _yield_job_to_queue(job)
                    return job
                slice_started_at = time.monotonic()

        return _mark_job_completed(job)
    finally:
        prepared_rows.close()


def process_next_ciudadanos_import_job() -> bool:
    try:
        mark_stale_ciudadanos_import_jobs_as_failed()
        job = claim_next_ciudadanos_import_job()
    except OperationalError:
        logger.exception(
            "No se pudieron consultar lotes pendientes de importacion de ciudadanos."
        )
        return False

    if not job:
        return False

    try:
        process_ciudadanos_import_job(job)
    except LostImportLease:
        logger.info("Otro worker recuperó el lote de ciudadanos #%s.", job.pk)
    return True


def run_ciudadanos_import_jobs_worker(*, once: bool = False) -> None:
    poll_seconds = get_ciudadanos_import_job_poll_seconds()
    while True:
        try:
            close_old_connections()
            processed_job = process_next_ciudadanos_import_job()
        except Exception:
            logger.exception("Fallo inesperado en el worker de importacion ciudadanos.")
            if once:
                raise
            processed_job = False
        finally:
            close_old_connections()
        if once:
            return
        if processed_job:
            continue
        time.sleep(poll_seconds)
