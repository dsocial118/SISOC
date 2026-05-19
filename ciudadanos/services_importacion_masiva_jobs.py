from __future__ import annotations

import logging
import os
import time
from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import OperationalError, models
from django.http import Http404
from django.utils import timezone

from ciudadanos.models import CiudadanosImportJob, CiudadanosImportJobRow
from ciudadanos.services_importacion_masiva import (
    build_ciudadanos_import_error_message,
    load_ciudadanos_import_rows,
    process_ciudadanos_import_row,
    validate_ciudadanos_import_workbook,
)

logger = logging.getLogger("django")
DEFAULT_CIUDADANOS_IMPORT_JOB_POLL_SECONDS = 5
DEFAULT_CIUDADANOS_IMPORT_JOB_STALE_SECONDS = 900
DEFAULT_CIUDADANOS_IMPORT_RENAPER_SLEEP_SECONDS = 1.0
STALE_JOB_ERROR_MESSAGE = (
    "El lote se interrumpio antes de finalizar. "
    "Puede reanudarlo desde la ultima fila pendiente."
)


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
    job.last_activity_at = timezone.now()
    job.save(
        update_fields=[
            "status",
            "last_error_message",
            "last_error_type",
            "last_error_at",
            "finished_at",
            "resume_count",
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
    for job in stale_jobs.iterator():
        now = timezone.now()
        job.status = CiudadanosImportJob.Status.FAILED
        job.last_error_message = STALE_JOB_ERROR_MESSAGE
        job.last_error_type = "stale_job"
        job.last_error_at = now
        job.finished_at = now
        job.last_activity_at = now
        job.save(
            update_fields=[
                "status",
                "last_error_message",
                "last_error_type",
                "last_error_at",
                "finished_at",
                "last_activity_at",
            ]
        )
        updated_count += 1
    return updated_count


def claim_next_ciudadanos_import_job() -> CiudadanosImportJob | None:
    candidate_ids = list(
        CiudadanosImportJob.objects.filter(status=CiudadanosImportJob.Status.PENDING)
        .order_by("requested_at", "id")
        .values_list("id", flat=True)[:20]
    )
    now = timezone.now()
    for job_id in candidate_ids:
        updated = CiudadanosImportJob.objects.filter(
            pk=job_id,
            status=CiudadanosImportJob.Status.PENDING,
        ).update(
            status=CiudadanosImportJob.Status.PROCESSING,
            finished_at=None,
            last_activity_at=now,
        )
        if not updated:
            continue

        job = CiudadanosImportJob.objects.get(pk=job_id)
        if not job.started_at:
            job.started_at = now
            job.save(update_fields=["started_at"])
        return job
    return None


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


def _sync_job_total_rows(*, job: CiudadanosImportJob, total_rows: int) -> None:
    if job.total_rows == total_rows and job.pending_rows == max(
        total_rows - job.processed_rows,
        0,
    ):
        return
    job.total_rows = total_rows
    _recalculate_job_counters(job)
    job.save(
        update_fields=[
            "total_rows",
            "processed_rows",
            "created_rows",
            "existing_rows",
            "failed_rows",
            "pending_rows",
        ]
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
    job.save(
        update_fields=[
            "status",
            "last_error_message",
            "last_error_type",
            "last_error_at",
            "finished_at",
            "last_activity_at",
        ]
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
    job.save(update_fields=update_fields)


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


def _get_job_row_log(*, job: CiudadanosImportJob, row):
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
    job.save(
        update_fields=[
            "status",
            "next_row_index",
            "last_attempted_row",
            "last_attempted_documento",
            "last_activity_at",
        ]
    )


def _apply_row_base_data(row_log: CiudadanosImportJobRow, row) -> None:
    row_log.documento_raw = row.documento_raw
    row_log.dni = row.dni
    row_log.cuil = row.cuil
    row_log.sexo = row.sexo


def _save_row_pending_after_systemic_error(
    *,
    job: CiudadanosImportJob,
    row_log: CiudadanosImportJobRow,
    row,
    result: dict[str, object],
) -> CiudadanosImportJob:
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
    job.save(
        update_fields=[
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
        ]
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
    _recalculate_job_counters(job)
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
    job.save(update_fields=update_fields)
    return job


def _mark_job_completed(job: CiudadanosImportJob) -> CiudadanosImportJob:
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
    job.save(
        update_fields=[
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
        ]
    )
    return job


def process_ciudadanos_import_job(
    job: CiudadanosImportJob,
) -> CiudadanosImportJob:
    _ensure_job_processing(job)
    rows = _load_job_rows(job)
    if rows is None:
        return job

    total_rows = len(rows)
    _sync_job_total_rows(job=job, total_rows=total_rows)
    if job.next_row_index >= total_rows:
        return _mark_job_completed(job)

    renaper_sleep_seconds = get_ciudadanos_import_renaper_sleep_seconds()
    for row_index in range(job.next_row_index, total_rows):
        row = rows[row_index]
        _start_job_row_attempt(job=job, row_index=row_index, row=row)
        row_log = _get_job_row_log(job=job, row=row)

        try:
            result = process_ciudadanos_import_row(
                row=row,
                requested_by=job.requested_by,
            )
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

        if result.get("systemic"):
            return _save_row_pending_after_systemic_error(
                job=job,
                row_log=row_log,
                row=row,
                result=result,
            )

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

    return _mark_job_completed(job)


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

    process_ciudadanos_import_job(job)
    return True


def run_ciudadanos_import_jobs_worker(*, once: bool = False) -> None:
    poll_seconds = get_ciudadanos_import_job_poll_seconds()
    while True:
        try:
            processed_job = process_next_ciudadanos_import_job()
        except Exception:
            logger.exception("Fallo inesperado en el worker de importacion ciudadanos.")
            if once:
                raise
            time.sleep(poll_seconds)
            continue
        if once:
            return
        if processed_job:
            continue
        time.sleep(poll_seconds)
