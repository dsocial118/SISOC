from __future__ import annotations

import logging
import os
import time
from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import OperationalError, models
from django.http import Http404
from django.utils import timezone

from users.models import BulkCredentialsJob, BulkCredentialsJobRow
from users.services_bulk_credentials import (
    _build_login_url,
    _load_workbook_rows,
    build_bulk_credentials_error_message,
    get_bulk_credentials_send_type_config,
    process_bulk_credentials_row,
    validate_bulk_credentials_workbook,
)

logger = logging.getLogger("django")
DEFAULT_BULK_CREDENTIALS_JOB_POLL_SECONDS = 2
DEFAULT_BULK_CREDENTIALS_JOB_STALE_SECONDS = 900
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


def get_bulk_credentials_job_poll_seconds() -> int:
    return _safe_positive_int(
        os.getenv("BULK_CREDENTIALS_JOB_POLL_SECONDS", ""),
        DEFAULT_BULK_CREDENTIALS_JOB_POLL_SECONDS,
    )


def get_bulk_credentials_job_stale_seconds() -> int:
    return _safe_positive_int(
        os.getenv("BULK_CREDENTIALS_JOB_STALE_SECONDS", ""),
        DEFAULT_BULK_CREDENTIALS_JOB_STALE_SECONDS,
    )


def create_bulk_credentials_job(*, uploaded_file, send_type: str | None, requested_by):
    send_type_config = validate_bulk_credentials_workbook(
        uploaded_file,
        send_type=send_type,
    )
    job = BulkCredentialsJob(
        requested_by=requested_by,
        original_filename=getattr(uploaded_file, "name", "credenciales.xlsx"),
        send_type=send_type_config.key,
    )
    uploaded_file.seek(0)
    job.archivo.save(job.original_filename, uploaded_file, save=False)
    job.save()
    return job


def get_bulk_credentials_job_queryset():
    return BulkCredentialsJob.objects.select_related("requested_by").order_by(
        "-requested_at", "-id"
    )


def get_recent_bulk_credentials_jobs(limit: int = 10, *, requested_by=None):
    queryset = get_bulk_credentials_job_queryset()
    if requested_by is not None:
        queryset = queryset.filter(requested_by=requested_by)
    return list(queryset[:limit])


def get_bulk_credentials_job_or_404(*, job_id: int):
    job = get_bulk_credentials_job_queryset().filter(pk=job_id).first()
    if not job:
        raise Http404("No existe el lote solicitado.")
    return job


def can_resume_bulk_credentials_job(job: BulkCredentialsJob) -> bool:
    return job.status == BulkCredentialsJob.Status.FAILED


def request_resume_bulk_credentials_job(
    *, job: BulkCredentialsJob
) -> BulkCredentialsJob:
    if not can_resume_bulk_credentials_job(job):
        raise ValidationError("Solo se pueden reanudar lotes fallidos.")

    job.status = BulkCredentialsJob.Status.PENDING
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


def mark_stale_bulk_credentials_jobs_as_failed() -> int:
    stale_threshold = timezone.now() - timedelta(
        seconds=get_bulk_credentials_job_stale_seconds()
    )
    stale_jobs = BulkCredentialsJob.objects.filter(
        status=BulkCredentialsJob.Status.PROCESSING,
    ).filter(
        models.Q(last_activity_at__isnull=True)
        | models.Q(last_activity_at__lt=stale_threshold)
    )
    updated_count = 0
    for job in stale_jobs.iterator():
        job.status = BulkCredentialsJob.Status.FAILED
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


def claim_next_bulk_credentials_job() -> BulkCredentialsJob | None:
    candidate_ids = list(
        BulkCredentialsJob.objects.filter(status=BulkCredentialsJob.Status.PENDING)
        .order_by("requested_at", "id")
        .values_list("id", flat=True)[:20]
    )
    now = timezone.now()
    for job_id in candidate_ids:
        updated = BulkCredentialsJob.objects.filter(
            pk=job_id,
            status=BulkCredentialsJob.Status.PENDING,
        ).update(
            status=BulkCredentialsJob.Status.PROCESSING,
            finished_at=None,
            last_activity_at=now,
        )
        if not updated:
            continue

        job = BulkCredentialsJob.objects.get(pk=job_id)
        if not job.started_at:
            job.started_at = now
            job.save(update_fields=["started_at"])
        return job
    return None


def _row_contribution(status: str | None, password_updated: bool) -> dict[str, int]:
    contribution = {
        "processed_rows": 0,
        "sent_rows": 0,
        "updated_password_rows": 0,
        "unchanged_password_rows": 0,
        "rejected_rows": 0,
    }
    if status == BulkCredentialsJobRow.Status.SENT:
        contribution["processed_rows"] = 1
        contribution["sent_rows"] = 1
        if password_updated:
            contribution["updated_password_rows"] = 1
        else:
            contribution["unchanged_password_rows"] = 1
    elif status == BulkCredentialsJobRow.Status.FAILED:
        contribution["processed_rows"] = 1
        contribution["rejected_rows"] = 1
    return contribution


def _apply_row_outcome(
    *,
    job: BulkCredentialsJob,
    old_status: str | None,
    old_password_updated: bool,
    new_status: str,
    new_password_updated: bool,
) -> None:
    old_contribution = _row_contribution(old_status, old_password_updated)
    new_contribution = _row_contribution(new_status, new_password_updated)
    for field_name, new_value in new_contribution.items():
        updated_value = (
            getattr(job, field_name) - old_contribution[field_name] + new_value
        )
        setattr(job, field_name, max(0, updated_value))


def _build_row_log_defaults(row) -> dict[str, object]:
    return {
        "usuario": row.usuario,
        "mail_destino": row.mail,
        "status": BulkCredentialsJobRow.Status.FAILED,
        "mensaje": "",
        "password_actualizada": False,
        "attempts": 0,
    }


def _sync_job_total_rows(*, job: BulkCredentialsJob, total_rows: int) -> None:
    if job.total_rows == total_rows:
        return
    job.total_rows = total_rows
    job.save(update_fields=["total_rows"])


def _mark_job_completed(*, job: BulkCredentialsJob) -> BulkCredentialsJob:
    now = timezone.now()
    job.status = BulkCredentialsJob.Status.COMPLETED
    job.finished_at = now
    job.last_activity_at = now
    job.last_error_message = ""
    job.last_error_at = None
    job.save(
        update_fields=[
            "status",
            "finished_at",
            "last_activity_at",
            "last_error_message",
            "last_error_at",
        ]
    )
    return job


def _start_job_row_attempt(*, job: BulkCredentialsJob, row_index: int, row) -> None:
    now = timezone.now()
    job.status = BulkCredentialsJob.Status.PROCESSING
    job.next_row_index = row_index
    job.last_attempted_row = row.fila
    job.last_attempted_username = row.usuario
    job.last_activity_at = now
    job.save(
        update_fields=[
            "status",
            "next_row_index",
            "last_attempted_row",
            "last_attempted_username",
            "last_activity_at",
        ]
    )


def _get_job_row_log(*, job: BulkCredentialsJob, row):
    row_log, created = BulkCredentialsJobRow.objects.get_or_create(
        job=job,
        fila=row.fila,
        defaults=_build_row_log_defaults(row),
    )
    return (
        row_log,
        (None if created else row_log.status),
        (False if created else row_log.password_actualizada),
    )


def _build_row_processing_state(*, row_log, old_status, old_password_updated):
    return {
        "row_log": row_log,
        "old_status": old_status,
        "old_password_updated": old_password_updated,
    }


def _build_row_progress(*, row_index: int, total_rows: int):
    next_row_index = row_index + 1
    return {
        "next_row_index": next_row_index,
        "is_last_row": next_row_index >= total_rows,
    }


def _save_failed_row_log(*, row_log: BulkCredentialsJobRow, row, message: str) -> None:
    row_log.usuario = row.usuario
    row_log.mail_destino = row.mail
    row_log.status = BulkCredentialsJobRow.Status.FAILED
    row_log.password_actualizada = False
    row_log.mensaje = message
    row_log.attempts += 1
    row_log.processed_at = timezone.now()
    row_log.save()


def _record_row_failure(
    *,
    job: BulkCredentialsJob,
    row,
    row_state,
    message: str,
) -> BulkCredentialsJob:
    row_log = row_state["row_log"]
    _save_failed_row_log(row_log=row_log, row=row, message=message)
    _apply_row_outcome(
        job=job,
        old_status=row_state["old_status"],
        old_password_updated=row_state["old_password_updated"],
        new_status=row_log.status,
        new_password_updated=row_log.password_actualizada,
    )

    now = timezone.now()
    job.status = BulkCredentialsJob.Status.FAILED
    job.last_error_message = message
    job.last_error_at = now
    job.finished_at = now
    job.last_activity_at = now
    job.save(
        update_fields=[
            "processed_rows",
            "sent_rows",
            "updated_password_rows",
            "unchanged_password_rows",
            "rejected_rows",
            "status",
            "last_error_message",
            "last_error_at",
            "finished_at",
            "last_activity_at",
        ]
    )
    return job


def _record_row_success(
    *,
    job: BulkCredentialsJob,
    row,
    row_state,
    result: dict[str, object],
    progress,
) -> BulkCredentialsJob:
    row_log = row_state["row_log"]
    row_log.usuario = row.usuario
    row_log.mail_destino = row.mail
    row_log.status = BulkCredentialsJobRow.Status.SENT
    row_log.password_actualizada = bool(result["password_actualizada"])
    row_log.mensaje = str(result["mensaje"])
    row_log.attempts += 1
    row_log.processed_at = timezone.now()
    row_log.save()

    _apply_row_outcome(
        job=job,
        old_status=row_state["old_status"],
        old_password_updated=row_state["old_password_updated"],
        new_status=row_log.status,
        new_password_updated=row_log.password_actualizada,
    )

    now = timezone.now()
    job.next_row_index = progress["next_row_index"]
    job.last_successful_row = row.fila
    job.last_successful_username = row.usuario
    job.last_activity_at = now
    update_fields = [
        "processed_rows",
        "sent_rows",
        "updated_password_rows",
        "unchanged_password_rows",
        "rejected_rows",
        "next_row_index",
        "last_successful_row",
        "last_successful_username",
        "last_activity_at",
    ]
    if progress["is_last_row"]:
        job.status = BulkCredentialsJob.Status.COMPLETED
        job.finished_at = now
        job.last_error_message = ""
        job.last_error_at = None
        update_fields.extend(
            [
                "status",
                "finished_at",
                "last_error_message",
                "last_error_at",
            ]
        )
    job.save(update_fields=update_fields)
    return job


def _record_job_level_failure(
    *,
    job: BulkCredentialsJob,
    message: str,
) -> BulkCredentialsJob:
    now = timezone.now()
    job.status = BulkCredentialsJob.Status.FAILED
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


def _load_job_rows(job: BulkCredentialsJob, *, send_type_config):
    try:
        job.archivo.open("rb")
        return _load_workbook_rows(
            job.archivo,
            send_type_config=send_type_config,
        )
    except ValidationError as exc:
        _record_job_level_failure(
            job=job,
            message=build_bulk_credentials_error_message(exc),
        )
    except Exception as exc:
        logger.exception(
            "Fallo leyendo archivo de lote de credenciales. job_id=%s",
            job.id,
        )
        _record_job_level_failure(
            job=job,
            message=build_bulk_credentials_error_message(exc),
        )
    finally:
        try:
            job.archivo.close()
        except Exception:
            pass
    return None


def process_bulk_credentials_job(job: BulkCredentialsJob) -> BulkCredentialsJob:
    send_type_config = get_bulk_credentials_send_type_config(job.send_type)
    login_url = _build_login_url()
    rows = _load_job_rows(job=job, send_type_config=send_type_config)
    if rows is None:
        return job

    total_rows = len(rows)
    _sync_job_total_rows(job=job, total_rows=total_rows)
    if job.next_row_index >= total_rows:
        return _mark_job_completed(job=job)

    for row_index in range(job.next_row_index, total_rows):
        row = rows[row_index]
        _start_job_row_attempt(job=job, row_index=row_index, row=row)
        row_log, old_status, old_password_updated = _get_job_row_log(job=job, row=row)
        row_state = _build_row_processing_state(
            row_log=row_log,
            old_status=old_status,
            old_password_updated=old_password_updated,
        )

        try:
            result = process_bulk_credentials_row(
                row=row,
                send_type_config=send_type_config,
                login_url=login_url,
                max_total_seconds=None,
            )
        except ValidationError as exc:
            return _record_row_failure(
                job=job,
                row=row,
                row_state=row_state,
                message=build_bulk_credentials_error_message(exc),
            )
        except Exception as exc:
            logger.exception(
                (
                    "Fallo inesperado procesando lote de credenciales. "
                    "job_id=%s fila=%s usuario=%s"
                ),
                job.id,
                row.fila,
                row.usuario,
            )
            return _record_row_failure(
                job=job,
                row=row,
                row_state=row_state,
                message=build_bulk_credentials_error_message(exc),
            )
        job = _record_row_success(
            job=job,
            row=row,
            row_state=row_state,
            result=result,
            progress=_build_row_progress(row_index=row_index, total_rows=total_rows),
        )
        if job.status == BulkCredentialsJob.Status.COMPLETED:
            return job

    return job


def process_next_bulk_credentials_job() -> bool:
    try:
        mark_stale_bulk_credentials_jobs_as_failed()
        job = claim_next_bulk_credentials_job()
    except OperationalError:
        logger.exception(
            "No se pudieron consultar lotes pendientes de credenciales masivas."
        )
        return False

    if not job:
        return False

    process_bulk_credentials_job(job)
    return True


def run_bulk_credentials_jobs_worker(*, once: bool = False) -> None:
    poll_seconds = get_bulk_credentials_job_poll_seconds()
    while True:
        try:
            processed_job = process_next_bulk_credentials_job()
        except Exception:
            logger.exception("Fallo inesperado en el worker de credenciales masivas.")
            if once:
                raise
            time.sleep(poll_seconds)
            continue
        if once:
            return
        if processed_job:
            continue
        time.sleep(poll_seconds)
