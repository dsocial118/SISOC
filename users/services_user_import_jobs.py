from __future__ import annotations

import logging
import os
import time
from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import OperationalError, models
from django.http import Http404
from django.utils import timezone

from users.models import UserImportJob, UserImportJobRow
from users.services_user_import import (
    build_user_import_error_message,
    load_user_import_rows,
    process_single_user_import_row,
)

logger = logging.getLogger("django")
DEFAULT_USER_IMPORT_JOB_POLL_SECONDS = 2
DEFAULT_USER_IMPORT_JOB_STALE_SECONDS = 900
STALE_JOB_ERROR_MESSAGE = (
    "El lote se interrumpio antes de finalizar. "
    "Puede reanudarlo desde la ultima fila pendiente."
)


def _safe_positive_int(value, default: int) -> int:
    try:
        parsed = int(str(value).strip())
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def get_user_import_job_poll_seconds() -> int:
    return _safe_positive_int(
        os.getenv("USER_IMPORT_JOB_POLL_SECONDS", ""),
        DEFAULT_USER_IMPORT_JOB_POLL_SECONDS,
    )


def get_user_import_job_stale_seconds() -> int:
    return _safe_positive_int(
        os.getenv("USER_IMPORT_JOB_STALE_SECONDS", ""),
        DEFAULT_USER_IMPORT_JOB_STALE_SECONDS,
    )


def get_user_import_job_queryset():
    return UserImportJob.objects.select_related("requested_by").order_by(
        "-requested_at", "-id"
    )


def get_recent_user_import_jobs(limit: int = 10, *, requested_by=None):
    queryset = get_user_import_job_queryset()
    if requested_by is not None:
        queryset = queryset.filter(requested_by=requested_by)
    return list(queryset[:limit])


def get_user_import_job_or_404(*, job_id: int) -> UserImportJob:
    job = get_user_import_job_queryset().filter(pk=job_id).first()
    if not job:
        raise Http404("No existe el lote solicitado.")
    return job


def can_resume_user_import_job(job: UserImportJob) -> bool:
    return job.status == UserImportJob.Status.FAILED


def request_resume_user_import_job(*, job: UserImportJob) -> UserImportJob:
    if not can_resume_user_import_job(job):
        raise ValidationError("Solo se pueden reanudar lotes fallidos.")

    job.status = UserImportJob.Status.PENDING
    job.last_error_message = ""
    job.last_error_at = None
    job.finished_at = None
    job.resume_count += 1
    job.last_activity_at = timezone.now()
    job.save(
        update_fields=[
            "status",
            "last_error_message",
            "last_error_at",
            "finished_at",
            "resume_count",
            "last_activity_at",
        ]
    )
    return job


def mark_stale_user_import_jobs_as_failed() -> int:
    stale_threshold = timezone.now() - timedelta(
        seconds=get_user_import_job_stale_seconds()
    )
    stale_jobs = UserImportJob.objects.filter(
        status=UserImportJob.Status.PROCESSING,
    ).filter(
        models.Q(last_activity_at__isnull=True)
        | models.Q(last_activity_at__lt=stale_threshold)
    )
    updated_count = 0
    for job in stale_jobs.iterator():
        job.status = UserImportJob.Status.FAILED
        job.last_error_message = STALE_JOB_ERROR_MESSAGE
        job.last_error_at = timezone.now()
        job.finished_at = timezone.now()
        job.save(
            update_fields=[
                "status",
                "last_error_message",
                "last_error_at",
                "finished_at",
            ]
        )
        updated_count += 1
    return updated_count


def claim_next_user_import_job() -> UserImportJob | None:
    candidate_ids = list(
        UserImportJob.objects.filter(status=UserImportJob.Status.PENDING)
        .order_by("requested_at", "id")
        .values_list("id", flat=True)[:20]
    )
    now = timezone.now()
    for job_id in candidate_ids:
        updated = UserImportJob.objects.filter(
            pk=job_id,
            status=UserImportJob.Status.PENDING,
        ).update(
            status=UserImportJob.Status.PROCESSING,
            finished_at=None,
            last_activity_at=now,
        )
        if not updated:
            continue

        job = UserImportJob.objects.get(pk=job_id)
        if not job.started_at:
            job.started_at = now
            job.save(update_fields=["started_at"])
        return job
    return None


def _load_job_rows(job: UserImportJob) -> list[dict] | None:
    try:
        job.archivo.open("rb")
        return load_user_import_rows(job.archivo)
    except ValidationError as exc:
        _record_job_level_failure(
            job=job,
            message=build_user_import_error_message(exc),
        )
    except Exception:
        logger.exception(
            "Fallo leyendo archivo de lote de importacion. job_id=%s", job.id
        )
        _record_job_level_failure(
            job=job,
            message="No se pudo leer el archivo del lote.",
        )
    finally:
        try:
            job.archivo.close()
        except Exception:
            pass
    return None


def _get_or_create_job_row(*, job: UserImportJob, row_data: dict) -> tuple:
    row_log, created = UserImportJobRow.objects.get_or_create(
        job=job,
        fila=row_data["fila"],
        defaults={
            "nombre": row_data.get("nombre", ""),
            "apellido": row_data.get("apellido", ""),
            "email": row_data.get("correo", ""),
            "rol": row_data.get("rol", ""),
            "status": UserImportJobRow.Status.PENDING,
        },
    )
    return row_log, (None if created else row_log.status)


def _start_job_row_attempt(
    *, job: UserImportJob, row_index: int, row_data: dict
) -> None:
    now = timezone.now()
    job.next_row_index = row_index
    job.last_attempted_row = row_data["fila"]
    job.last_attempted_email = row_data.get("correo", "")
    job.last_activity_at = now
    job.save(
        update_fields=[
            "next_row_index",
            "last_attempted_row",
            "last_attempted_email",
            "last_activity_at",
        ]
    )


def _record_row_skipped(  # pylint: disable=too-many-arguments
    *,
    job: UserImportJob,
    row_log: UserImportJobRow,
    old_status,
    message: str,
    row_index: int,
    total_rows: int,
) -> UserImportJob:
    if old_status == UserImportJobRow.Status.SKIPPED:
        pass
    else:
        if old_status == UserImportJobRow.Status.FAILED:
            job.failed_rows = max(0, job.failed_rows - 1)
        elif old_status == UserImportJobRow.Status.CREATED:
            job.created_rows = max(0, job.created_rows - 1)
        job.skipped_rows += 1
        if old_status in (None, UserImportJobRow.Status.PENDING):
            job.processed_rows += 1

    row_log.status = UserImportJobRow.Status.SKIPPED
    row_log.mensaje = message
    row_log.attempts += 1
    row_log.processed_at = timezone.now()
    row_log.save()

    next_row_index = row_index + 1
    job.next_row_index = next_row_index
    job.last_activity_at = timezone.now()
    update_fields = [
        "processed_rows",
        "created_rows",
        "skipped_rows",
        "failed_rows",
        "next_row_index",
        "last_activity_at",
    ]

    if next_row_index >= total_rows:
        final_status = (
            UserImportJob.Status.COMPLETED_WITH_ERRORS
            if job.failed_rows > 0
            else UserImportJob.Status.COMPLETED
        )
        job.status = final_status
        job.finished_at = timezone.now()
        job.last_error_message = ""
        job.last_error_at = None
        update_fields.extend(
            ["status", "finished_at", "last_error_message", "last_error_at"]
        )

    job.save(update_fields=update_fields)
    return job


def _record_row_created(  # pylint: disable=too-many-arguments
    *,
    job: UserImportJob,
    row_log: UserImportJobRow,
    old_status,
    result: dict,
    row_index: int,
    total_rows: int,
) -> UserImportJob:
    if old_status == UserImportJobRow.Status.CREATED:
        pass
    else:
        if old_status == UserImportJobRow.Status.FAILED:
            job.failed_rows = max(0, job.failed_rows - 1)
        elif old_status == UserImportJobRow.Status.SKIPPED:
            job.skipped_rows = max(0, job.skipped_rows - 1)
        job.created_rows += 1
        if old_status in (None, UserImportJobRow.Status.PENDING):
            job.processed_rows += 1

    row_log.status = UserImportJobRow.Status.CREATED
    row_log.mensaje = result["mensaje"]
    row_log.email = result.get("email", row_log.email)
    row_log.attempts += 1
    row_log.processed_at = timezone.now()
    row_log.save()

    next_row_index = row_index + 1
    job.next_row_index = next_row_index
    job.last_successful_row = row_log.fila
    job.last_successful_email = row_log.email
    job.last_activity_at = timezone.now()
    update_fields = [
        "processed_rows",
        "created_rows",
        "skipped_rows",
        "failed_rows",
        "next_row_index",
        "last_successful_row",
        "last_successful_email",
        "last_activity_at",
    ]

    if next_row_index >= total_rows:
        final_status = (
            UserImportJob.Status.COMPLETED_WITH_ERRORS
            if job.failed_rows > 0
            else UserImportJob.Status.COMPLETED
        )
        job.status = final_status
        job.finished_at = timezone.now()
        job.last_error_message = ""
        job.last_error_at = None
        update_fields.extend(
            ["status", "finished_at", "last_error_message", "last_error_at"]
        )

    job.save(update_fields=update_fields)
    return job


def _record_row_failure(
    *, job: UserImportJob, row_log: UserImportJobRow, old_status, message: str
) -> UserImportJob:
    if old_status == UserImportJobRow.Status.CREATED:
        job.created_rows = max(0, job.created_rows - 1)
    elif old_status == UserImportJobRow.Status.SKIPPED:
        job.skipped_rows = max(0, job.skipped_rows - 1)

    if old_status != UserImportJobRow.Status.FAILED:
        job.failed_rows += 1
    if old_status in (None, UserImportJobRow.Status.PENDING):
        job.processed_rows += 1

    row_log.status = UserImportJobRow.Status.FAILED
    row_log.mensaje = message
    row_log.attempts += 1
    row_log.processed_at = timezone.now()
    row_log.save()

    now = timezone.now()
    job.status = UserImportJob.Status.FAILED
    job.last_error_message = message
    job.last_error_at = now
    job.finished_at = now
    job.last_activity_at = now
    job.save(
        update_fields=[
            "processed_rows",
            "created_rows",
            "skipped_rows",
            "failed_rows",
            "status",
            "last_error_message",
            "last_error_at",
            "finished_at",
            "last_activity_at",
        ]
    )
    return job


def _record_job_level_failure(*, job: UserImportJob, message: str) -> UserImportJob:
    now = timezone.now()
    job.status = UserImportJob.Status.FAILED
    job.last_error_message = message
    job.last_error_at = now
    job.finished_at = now
    job.last_activity_at = now
    job.save(
        update_fields=[
            "status",
            "last_error_message",
            "last_error_at",
            "finished_at",
            "last_activity_at",
        ]
    )
    return job


def process_user_import_job(job: UserImportJob) -> UserImportJob:
    rows = _load_job_rows(job)
    if rows is None:
        return job

    total_rows = len(rows)
    if job.total_rows != total_rows:
        job.total_rows = total_rows
        job.save(update_fields=["total_rows"])

    if job.next_row_index >= total_rows:
        now = timezone.now()
        job.status = UserImportJob.Status.COMPLETED
        job.finished_at = now
        job.last_activity_at = now
        job.save(update_fields=["status", "finished_at", "last_activity_at"])
        return job

    for row_index in range(job.next_row_index, total_rows):
        row_data = rows[row_index]
        _start_job_row_attempt(job=job, row_index=row_index, row_data=row_data)
        row_log, old_status = _get_or_create_job_row(job=job, row_data=row_data)

        try:
            result = process_single_user_import_row(row_data=row_data, job=job)
        except ValidationError as exc:
            return _record_row_failure(
                job=job,
                row_log=row_log,
                old_status=old_status,
                message=build_user_import_error_message(exc),
            )
        except Exception:
            logger.exception(
                "Fallo inesperado procesando lote de importacion. job_id=%s fila=%s",
                job.id,
                row_data.get("fila"),
            )
            return _record_row_failure(
                job=job,
                row_log=row_log,
                old_status=old_status,
                message="Ocurrio un error inesperado al procesar la fila.",
            )

        row_status = result["status"]

        if row_status == UserImportJobRow.Status.SKIPPED:
            job = _record_row_skipped(
                job=job,
                row_log=row_log,
                old_status=old_status,
                message=result["mensaje"],
                row_index=row_index,
                total_rows=total_rows,
            )
        else:
            job = _record_row_created(
                job=job,
                row_log=row_log,
                old_status=old_status,
                result=result,
                row_index=row_index,
                total_rows=total_rows,
            )

        if job.status in (
            UserImportJob.Status.COMPLETED,
            UserImportJob.Status.COMPLETED_WITH_ERRORS,
        ):
            return job

    return job


def process_next_user_import_job() -> bool:
    try:
        mark_stale_user_import_jobs_as_failed()
        job = claim_next_user_import_job()
    except OperationalError:
        logger.exception(
            "No se pudieron consultar lotes pendientes de importacion de usuarios."
        )
        return False

    if not job:
        return False

    process_user_import_job(job)
    return True


def run_user_import_jobs_worker(*, once: bool = False) -> None:
    poll_seconds = get_user_import_job_poll_seconds()
    while True:
        try:
            processed_job = process_next_user_import_job()
        except Exception:
            logger.exception(
                "Fallo inesperado en el worker de importacion de usuarios."
            )
            if once:
                raise
            time.sleep(poll_seconds)
            continue
        if once:
            return
        if processed_job:
            continue
        time.sleep(poll_seconds)
