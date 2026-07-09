from __future__ import annotations

import logging
import mimetypes
import os
import time
from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import OperationalError, models
from django.http import Http404
from django.utils import timezone

from comunicados.models import MailingJob, MailingJobRow, MailingJobAttachment
from comunicados.services_mailing import (
    _load_mailing_workbook_rows,
    build_mailing_error_message,
    process_mailing_row,
    validate_mailing_workbook,
)

logger = logging.getLogger("django")
DEFAULT_MAILING_JOB_POLL_SECONDS = 2
DEFAULT_MAILING_JOB_STALE_SECONDS = 900
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


def get_mailing_job_poll_seconds() -> int:
    return _safe_positive_int(
        os.getenv("MAILING_JOB_POLL_SECONDS", ""),
        DEFAULT_MAILING_JOB_POLL_SECONDS,
    )


def get_mailing_job_stale_seconds() -> int:
    return _safe_positive_int(
        os.getenv("MAILING_JOB_STALE_SECONDS", ""),
        DEFAULT_MAILING_JOB_STALE_SECONDS,
    )


def create_mailing_job(
    *, uploaded_file, asunto: str, cuerpo: str, requested_by, attachments=None
):
    validate_mailing_workbook(uploaded_file)
    job = MailingJob(
        requested_by=requested_by,
        original_filename=getattr(uploaded_file, "name", "mailing.xlsx"),
        asunto=asunto,
        cuerpo=cuerpo,
    )
    uploaded_file.seek(0)
    job.archivo.save(job.original_filename, uploaded_file, save=False)
    job.save()

    if attachments:
        for attachment_file in attachments:
            MailingJobAttachment.objects.create(
                job=job,
                archivo=attachment_file,
                nombre_original=attachment_file.name,
            )
    return job


def get_mailing_job_queryset():
    return MailingJob.objects.select_related("requested_by").order_by(
        "-requested_at", "-id"
    )


def get_recent_mailing_jobs(limit: int = 10, *, requested_by=None):
    queryset = get_mailing_job_queryset()
    if requested_by is not None:
        queryset = queryset.filter(requested_by=requested_by)
    return list(queryset[:limit])


def get_mailing_job_or_404(*, job_id: int):
    job = get_mailing_job_queryset().filter(pk=job_id).first()
    if not job:
        raise Http404("No existe el lote solicitado.")
    return job


def can_resume_mailing_job(job: MailingJob) -> bool:
    return job.status == MailingJob.Status.FAILED


def request_resume_mailing_job(*, job: MailingJob) -> MailingJob:
    if not can_resume_mailing_job(job):
        raise ValidationError("Solo se pueden reanudar lotes fallidos.")

    job.status = MailingJob.Status.PENDING
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


def mark_stale_mailing_jobs_as_failed() -> int:
    stale_threshold = timezone.now() - timedelta(
        seconds=get_mailing_job_stale_seconds()
    )
    stale_jobs = MailingJob.objects.filter(
        status=MailingJob.Status.PROCESSING,
    ).filter(
        models.Q(last_activity_at__isnull=True)
        | models.Q(last_activity_at__lt=stale_threshold)
    )
    updated_count = 0
    for job in stale_jobs.iterator():
        job.status = MailingJob.Status.FAILED
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


def claim_next_mailing_job() -> MailingJob | None:
    candidate_ids = list(
        MailingJob.objects.filter(status=MailingJob.Status.PENDING)
        .order_by("requested_at", "id")
        .values_list("id", flat=True)[:20]
    )
    now = timezone.now()
    for job_id in candidate_ids:
        updated = MailingJob.objects.filter(
            pk=job_id,
            status=MailingJob.Status.PENDING,
        ).update(
            status=MailingJob.Status.PROCESSING,
            finished_at=None,
            last_activity_at=now,
        )
        if not updated:
            continue

        job = MailingJob.objects.get(pk=job_id)
        if not job.started_at:
            job.started_at = now
            job.save(update_fields=["started_at"])
        return job
    return None


def _row_contribution(status: str | None) -> dict[str, int]:
    contribution = {
        "processed_rows": 0,
        "sent_rows": 0,
        "rejected_rows": 0,
    }
    if status == MailingJobRow.Status.SENT:
        contribution["processed_rows"] = 1
        contribution["sent_rows"] = 1
    elif status == MailingJobRow.Status.FAILED:
        contribution["processed_rows"] = 1
        contribution["rejected_rows"] = 1
    return contribution


def _apply_row_outcome(
    *,
    job: MailingJob,
    old_status: str | None,
    new_status: str,
) -> None:
    old_contribution = _row_contribution(old_status)
    new_contribution = _row_contribution(new_status)
    for field_name, new_value in new_contribution.items():
        updated_value = (
            getattr(job, field_name) - old_contribution[field_name] + new_value
        )
        setattr(job, field_name, max(0, updated_value))


def _build_row_log_defaults(row) -> dict[str, object]:
    return {
        "mail_destino": row.mail,
        "status": MailingJobRow.Status.FAILED,
        "mensaje": "",
        "attempts": 0,
    }


def _sync_job_total_rows(*, job: MailingJob, total_rows: int) -> None:
    if job.total_rows == total_rows:
        return
    job.total_rows = total_rows
    job.save(update_fields=["total_rows"])


def _mark_job_completed(*, job: MailingJob) -> MailingJob:
    now = timezone.now()
    job.status = MailingJob.Status.COMPLETED
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


def _start_job_row_attempt(*, job: MailingJob, row_index: int, row) -> None:
    now = timezone.now()
    job.status = MailingJob.Status.PROCESSING
    job.next_row_index = row_index
    job.last_attempted_row = row.fila
    job.last_attempted_mail = row.mail
    job.last_activity_at = now
    job.save(
        update_fields=[
            "status",
            "next_row_index",
            "last_attempted_row",
            "last_attempted_mail",
            "last_activity_at",
        ]
    )


def _get_job_row_log(*, job: MailingJob, row):
    row_log, created = MailingJobRow.objects.get_or_create(
        job=job,
        fila=row.fila,
        defaults=_build_row_log_defaults(row),
    )
    return (
        row_log,
        (None if created else row_log.status),
    )


def _build_row_processing_state(*, row_log, old_status):
    return {
        "row_log": row_log,
        "old_status": old_status,
    }


def _build_row_progress(*, row_index: int, total_rows: int):
    next_row_index = row_index + 1
    return {
        "next_row_index": next_row_index,
        "is_last_row": next_row_index >= total_rows,
    }


def _save_failed_row_log(*, row_log: MailingJobRow, row, message: str) -> None:
    row_log.mail_destino = row.mail
    row_log.status = MailingJobRow.Status.FAILED
    row_log.mensaje = message
    row_log.attempts += 1
    row_log.processed_at = timezone.now()
    row_log.save()


def _record_row_failure(
    *,
    job: MailingJob,
    row,
    row_state,
    message: str,
) -> MailingJob:
    row_log = row_state["row_log"]
    _save_failed_row_log(row_log=row_log, row=row, message=message)
    _apply_row_outcome(
        job=job,
        old_status=row_state["old_status"],
        new_status=row_log.status,
    )

    now = timezone.now()
    job.status = MailingJob.Status.FAILED
    job.last_error_message = message
    job.last_error_at = now
    job.finished_at = now
    job.last_activity_at = now
    job.save(
        update_fields=[
            "processed_rows",
            "sent_rows",
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
    job: MailingJob,
    row,
    row_state,
    result: dict[str, object],
    progress,
) -> MailingJob:
    row_log = row_state["row_log"]
    row_log.mail_destino = str(result["mail_destino"])
    row_log.status = MailingJobRow.Status.SENT
    row_log.mensaje = str(result["mensaje"])
    row_log.attempts += 1
    row_log.processed_at = timezone.now()
    row_log.save()

    _apply_row_outcome(
        job=job,
        old_status=row_state["old_status"],
        new_status=row_log.status,
    )

    now = timezone.now()
    job.next_row_index = progress["next_row_index"]
    job.last_successful_row = row.fila
    job.last_successful_mail = row.mail
    job.last_activity_at = now
    update_fields = [
        "processed_rows",
        "sent_rows",
        "rejected_rows",
        "next_row_index",
        "last_successful_row",
        "last_successful_mail",
        "last_activity_at",
    ]
    if progress["is_last_row"]:
        job.status = MailingJob.Status.COMPLETED
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
    job: MailingJob,
    message: str,
) -> MailingJob:
    now = timezone.now()
    job.status = MailingJob.Status.FAILED
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


def _load_job_rows(job: MailingJob):
    try:
        job.archivo.open("rb")
        return _load_mailing_workbook_rows(job.archivo)
    except ValidationError as exc:
        _record_job_level_failure(
            job=job,
            message=build_mailing_error_message(exc),
        )
    except Exception as exc:
        logger.exception(
            "Fallo leyendo archivo de lote de mailing. job_id=%s",
            job.id,
        )
        _record_job_level_failure(
            job=job,
            message=build_mailing_error_message(exc),
        )
    finally:
        try:
            job.archivo.close()
        except Exception:
            pass
    return None


def process_mailing_job(job: MailingJob) -> MailingJob:
    rows = _load_job_rows(job=job)
    if rows is None:
        return job

    # Cache attachments in memory
    cached_attachments = []
    for attachment in job.attachments.all():
        try:
            attachment.archivo.open("rb")
            content = attachment.archivo.read()
            mimetype, _ = mimetypes.guess_type(attachment.nombre_original)
            cached_attachments.append(
                (
                    attachment.nombre_original,
                    content,
                    mimetype or "application/octet-stream",
                )
            )
        finally:
            attachment.archivo.close()

    total_rows = len(rows)
    _sync_job_total_rows(job=job, total_rows=total_rows)
    if job.next_row_index >= total_rows:
        return _mark_job_completed(job=job)

    for row_index in range(job.next_row_index, total_rows):
        row = rows[row_index]
        _start_job_row_attempt(job=job, row_index=row_index, row=row)
        row_log, old_status = _get_job_row_log(job=job, row=row)
        row_state = _build_row_processing_state(
            row_log=row_log,
            old_status=old_status,
        )

        try:
            result = process_mailing_row(
                row=row,
                asunto=job.asunto,
                cuerpo=job.cuerpo,
                attachments=cached_attachments,
            )
        except ValidationError as exc:
            return _record_row_failure(
                job=job,
                row=row,
                row_state=row_state,
                message=build_mailing_error_message(exc),
            )
        except Exception as exc:
            logger.exception(
                (
                    "Fallo inesperado procesando lote de mailing. "
                    "job_id=%s fila=%s mail=%s"
                ),
                job.id,
                row.fila,
                row.mail,
            )
            return _record_row_failure(
                job=job,
                row=row,
                row_state=row_state,
                message=build_mailing_error_message(exc),
            )
        job = _record_row_success(
            job=job,
            row=row,
            row_state=row_state,
            result=result,
            progress=_build_row_progress(row_index=row_index, total_rows=total_rows),
        )
        if job.status == MailingJob.Status.COMPLETED:
            return job

    return job


def process_next_mailing_job() -> bool:
    try:
        mark_stale_mailing_jobs_as_failed()
        job = claim_next_mailing_job()
    except OperationalError:
        logger.exception("No se pudieron consultar lotes pendientes de mailing.")
        return False

    if not job:
        return False

    process_mailing_job(job)
    return True


def run_mailing_jobs_worker(*, once: bool = False) -> None:
    poll_seconds = get_mailing_job_poll_seconds()
    while True:
        try:
            processed_job = process_next_mailing_job()
        except Exception:
            logger.exception("Fallo inesperado en el worker de mailing.")
            if once:
                raise
            time.sleep(poll_seconds)
            continue
        if once:
            return
        if processed_job:
            continue
        time.sleep(poll_seconds)
