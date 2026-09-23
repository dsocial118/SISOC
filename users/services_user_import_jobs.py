from __future__ import annotations

import logging
import os
import time
import uuid
from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import (
    DatabaseError,
    OperationalError,
    close_old_connections,
    models,
    transaction,
)
from django.db.models.functions import Coalesce
from django.http import Http404
from django.utils import timezone

from users.models import UserImportJob, UserImportJobRow
from users.services_user_import import (
    build_user_import_error_message,
    load_user_import_rows,
    process_single_user_import_row,
    send_user_import_job_credentials,
)

logger = logging.getLogger("django")
DEFAULT_USER_IMPORT_JOB_POLL_SECONDS = 2
DEFAULT_USER_IMPORT_JOB_STALE_SECONDS = 900
DEFAULT_USER_IMPORT_JOB_SLICE_SECONDS = 300


class LostImportLease(RuntimeError):
    """Otro worker recuperó el lote; este proceso no debe persistir filas."""


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


def get_user_import_job_slice_seconds() -> int:
    return _safe_positive_int(
        os.getenv("USER_IMPORT_JOB_SLICE_SECONDS", ""),
        DEFAULT_USER_IMPORT_JOB_SLICE_SECONDS,
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
    job.lease_token = None
    job.last_activity_at = timezone.now()
    job.save(
        update_fields=[
            "status",
            "last_error_message",
            "last_error_at",
            "finished_at",
            "resume_count",
            "lease_token",
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
    for job_id, lease_token in list(stale_jobs.values_list("pk", "lease_token")):
        updated_count += (
            UserImportJob.objects.filter(
                pk=job_id,
                status=UserImportJob.Status.PROCESSING,
                lease_token=lease_token,
            )
            .filter(
                models.Q(last_activity_at__isnull=True)
                | models.Q(last_activity_at__lt=stale_threshold)
            )
            .update(
                status=UserImportJob.Status.PENDING,
                lease_token=None,
                resume_count=models.F("resume_count") + 1,
                last_activity_at=timezone.now(),
            )
        )
    return updated_count


def claim_next_user_import_job() -> UserImportJob | None:
    candidate_ids = list(
        UserImportJob.objects.filter(status=UserImportJob.Status.PENDING)
        .annotate(queue_time=Coalesce("last_activity_at", "requested_at"))
        .order_by("queue_time", "id")
        .values_list("id", flat=True)[:20]
    )
    now = timezone.now()
    for job_id in candidate_ids:
        lease_token = uuid.uuid4()
        updated = UserImportJob.objects.filter(
            pk=job_id,
            status=UserImportJob.Status.PENDING,
        ).update(
            status=UserImportJob.Status.PROCESSING,
            finished_at=None,
            last_activity_at=now,
            lease_token=lease_token,
        )
        if not updated:
            continue

        job = UserImportJob.objects.get(pk=job_id)
        if not job.started_at:
            job.started_at = now
            job.save(update_fields=["started_at"])
        return job
    return None


def _lock_owned_job(job: UserImportJob) -> None:
    if job.lease_token is None:
        raise LostImportLease(f"El worker no reclamó el lote #{job.pk}.")
    current = UserImportJob.objects.select_for_update().get(pk=job.pk)
    if (
        current.status != UserImportJob.Status.PROCESSING
        or current.lease_token != job.lease_token
    ):
        raise LostImportLease(f"El worker perdió el lote #{job.pk}.")


def _save_owned_job(job: UserImportJob, update_fields: list[str]) -> None:
    if job.lease_token is None:
        raise LostImportLease(f"El worker no reclamó el lote #{job.pk}.")
    updated = UserImportJob.objects.filter(
        pk=job.pk,
        status=UserImportJob.Status.PROCESSING,
        lease_token=job.lease_token,
    ).update(**{field: getattr(job, field) for field in update_fields})
    if not updated:
        raise LostImportLease(f"El worker perdió el lote #{job.pk}.")


def _ensure_job_claimed(job: UserImportJob) -> None:
    """Permite el procesamiento directo sólo si el lote sigue pendiente."""
    if job.lease_token is not None:
        return
    token = uuid.uuid4()
    updated = UserImportJob.objects.filter(
        pk=job.pk,
        status=UserImportJob.Status.PENDING,
        lease_token__isnull=True,
    ).update(
        status=UserImportJob.Status.PROCESSING,
        lease_token=token,
        last_activity_at=timezone.now(),
    )
    if not updated:
        raise LostImportLease(f"El worker no pudo reclamar el lote #{job.pk}.")
    job.lease_token = token
    job.status = UserImportJob.Status.PROCESSING


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
    _save_owned_job(
        job,
        [
            "next_row_index",
            "last_attempted_row",
            "last_attempted_email",
            "last_activity_at",
        ],
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

    _save_owned_job(job, update_fields)
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
    created_user_id = result.get("created_user_id")
    if created_user_id:
        row_log.created_user_id = created_user_id
    row_log.attempts += 1
    row_log.processed_at = timezone.now()
    update_fields = ["status", "mensaje", "email", "attempts", "processed_at"]
    if created_user_id:
        update_fields.append("created_user")
    row_log.save(update_fields=update_fields)

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

    _save_owned_job(job, update_fields)
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
    _save_owned_job(
        job,
        [
            "processed_rows",
            "created_rows",
            "skipped_rows",
            "failed_rows",
            "status",
            "last_error_message",
            "last_error_at",
            "finished_at",
            "last_activity_at",
        ],
    )
    return job


def _record_job_level_failure(*, job: UserImportJob, message: str) -> UserImportJob:
    now = timezone.now()
    job.status = UserImportJob.Status.FAILED
    job.last_error_message = message
    job.last_error_at = now
    job.finished_at = now
    job.last_activity_at = now
    _save_owned_job(
        job,
        [
            "status",
            "last_error_message",
            "last_error_at",
            "finished_at",
            "last_activity_at",
        ],
    )
    return job


def _send_credentials_if_needed(job: UserImportJob) -> UserImportJob:
    if not job.send_credentials:
        return job
    try:
        send_user_import_job_credentials(job)
    except Exception:
        logger.exception(
            "Fallo inesperado enviando credenciales de importacion job_id=%s", job.id
        )
    return job


@transaction.atomic
def _yield_job_to_queue(job: UserImportJob) -> None:
    _lock_owned_job(job)
    now = timezone.now()
    updated = UserImportJob.objects.filter(
        pk=job.pk,
        status=UserImportJob.Status.PROCESSING,
        lease_token=job.lease_token,
    ).update(
        status=UserImportJob.Status.PENDING,
        lease_token=None,
        last_activity_at=now,
    )
    if not updated:
        raise LostImportLease(f"El worker perdió el lote #{job.pk}.")
    job.status = UserImportJob.Status.PENDING
    job.lease_token = None
    job.last_activity_at = now


def process_user_import_job(job: UserImportJob) -> UserImportJob:
    if job.status in (
        UserImportJob.Status.COMPLETED,
        UserImportJob.Status.COMPLETED_WITH_ERRORS,
    ):
        return _send_credentials_if_needed(job)
    _ensure_job_claimed(job)
    slice_seconds = get_user_import_job_slice_seconds()
    slice_started_at = time.monotonic()
    rows = _load_job_rows(job)
    if rows is None:
        return job

    total_rows = len(rows)
    if job.total_rows != total_rows:
        job.total_rows = total_rows
        _save_owned_job(job, ["total_rows"])

    if job.next_row_index >= total_rows:
        now = timezone.now()
        job.status = (
            UserImportJob.Status.COMPLETED_WITH_ERRORS
            if job.failed_rows > 0
            else UserImportJob.Status.COMPLETED
        )
        job.finished_at = now
        job.last_activity_at = now
        _save_owned_job(job, ["status", "finished_at", "last_activity_at"])
        return _send_credentials_if_needed(job)

    for row_index in range(job.next_row_index, total_rows):
        close_old_connections()
        row_data = rows[row_index]
        _start_job_row_attempt(job=job, row_index=row_index, row_data=row_data)
        with transaction.atomic():
            _lock_owned_job(job)
            row_log, old_status = _get_or_create_job_row(job=job, row_data=row_data)

            try:
                result = process_single_user_import_row(row_data=row_data, job=job)
            except DatabaseError:
                raise
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

            if result["status"] == UserImportJobRow.Status.SKIPPED:
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
            return _send_credentials_if_needed(job)

        if time.monotonic() - slice_started_at >= slice_seconds:
            if (
                UserImportJob.objects.filter(status=UserImportJob.Status.PENDING)
                .exclude(pk=job.pk)
                .exists()
            ):
                _yield_job_to_queue(job)
                return job
            slice_started_at = time.monotonic()

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

    try:
        process_user_import_job(job)
    except LostImportLease:
        logger.info("Otro worker recuperó el lote de usuarios #%s.", job.pk)
    return True


def run_user_import_jobs_worker(*, once: bool = False) -> None:
    poll_seconds = get_user_import_job_poll_seconds()
    while True:
        try:
            close_old_connections()
            processed_job = process_next_user_import_job()
        except Exception:
            logger.exception(
                "Fallo inesperado en el worker de importacion de usuarios."
            )
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
