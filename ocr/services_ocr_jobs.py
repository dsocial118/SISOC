from __future__ import annotations

import logging
import os
import time
from datetime import timedelta

from django.db import models
from django.utils import timezone

from ocr.models import OCRJob, OCRJobDocument
from ocr.services_ocr import extract_text_from_file

logger = logging.getLogger("django")

DEFAULT_OCR_JOB_POLL_SECONDS = 2
DEFAULT_OCR_JOB_STALE_SECONDS = 600


def _safe_positive_int(value, default: int) -> int:
    try:
        parsed = int(str(value).strip())
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def get_ocr_job_poll_seconds() -> int:
    return _safe_positive_int(
        os.getenv("OCR_JOB_POLL_SECONDS", ""),
        DEFAULT_OCR_JOB_POLL_SECONDS,
    )


def get_ocr_job_stale_seconds() -> int:
    return _safe_positive_int(
        os.getenv("OCR_JOB_STALE_SECONDS", ""),
        DEFAULT_OCR_JOB_STALE_SECONDS,
    )


def create_ocr_job(*, requested_by, files: list) -> OCRJob:
    """Crea un OCRJob con sus documentos a partir de una lista de archivos subidos."""
    job = OCRJob(
        requested_by=requested_by,
        total_documents=len(files),
    )
    job.save()

    for uploaded_file in files:
        doc = OCRJobDocument(
            job=job,
            original_filename=uploaded_file.name,
            file_size=uploaded_file.size,
        )
        doc.archivo.save(uploaded_file.name, uploaded_file, save=False)
        doc.save()

    return job


def get_recent_ocr_jobs(limit: int = 10, *, requested_by=None):
    queryset = OCRJob.objects.select_related("requested_by").order_by(
        "-requested_at", "-id"
    )
    if requested_by is not None:
        queryset = queryset.filter(requested_by=requested_by)
    return list(queryset[:limit])


def mark_stale_ocr_jobs_as_failed() -> int:
    """Marca como fallidos los jobs en estado 'processing' sin actividad reciente."""
    stale_seconds = get_ocr_job_stale_seconds()
    cutoff = timezone.now() - timedelta(seconds=stale_seconds)
    updated = OCRJob.objects.filter(
        status=OCRJob.Status.PROCESSING,
        last_activity_at__lt=cutoff,
    ).update(
        status=OCRJob.Status.FAILED,
        last_error_message=(
            "El lote se interrumpió antes de finalizar (timeout de worker)."
        ),
        finished_at=timezone.now(),
    )
    if updated:
        logger.warning("[ocr] %s lote(s) marcados como fallidos por inactividad.", updated)
    return updated


def claim_next_ocr_job() -> OCRJob | None:
    """
    Reclama atómicamente el próximo job pendiente.
    Itera candidatos de más antiguo a más nuevo hasta lograr reclamar uno.
    Retorna None si no hay jobs pendientes.
    """
    candidates = list(
        OCRJob.objects.filter(status=OCRJob.Status.PENDING)
        .order_by("requested_at", "id")[:20]
        .values_list("id", flat=True)
    )
    if not candidates:
        return None

    now = timezone.now()
    for candidate_id in candidates:
        updated = OCRJob.objects.filter(
            pk=candidate_id,
            status=OCRJob.Status.PENDING,
        ).update(
            status=OCRJob.Status.PROCESSING,
            started_at=now,
            last_activity_at=now,
        )
        if updated:
            return OCRJob.objects.get(pk=candidate_id)

    return None


def _process_document(doc: OCRJobDocument) -> bool:
    """
    Procesa un documento individual. Retorna True si fue exitoso.
    Siempre borra el archivo de disco al finalizar (éxito o fallo).
    """
    now = timezone.now()
    doc.status = OCRJobDocument.Status.PROCESSING
    doc.save(update_fields=["status"])

    file_path = None
    try:
        if doc.archivo and doc.archivo.name:
            file_path = doc.archivo.path
        else:
            raise FileNotFoundError("No hay archivo asociado al documento.")

        result = extract_text_from_file(
            file_path=file_path,
            original_filename=doc.original_filename,
        )

        if result["text"]:
            doc.status = OCRJobDocument.Status.COMPLETED
        else:
            doc.status = OCRJobDocument.Status.NO_TEXT
            doc.error_message = result.get("warning", "")

        doc.extracted_text = result["text"]
        doc.page_count = result.get("page_count")
        doc.processed_at = now
        doc.save(
            update_fields=[
                "status",
                "extracted_text",
                "page_count",
                "error_message",
                "processed_at",
            ]
        )
        return True

    except Exception as exc:
        logger.exception("[ocr] Error procesando documento %s: %s", doc.id, exc)
        doc.status = OCRJobDocument.Status.FAILED
        doc.error_message = str(exc)
        doc.processed_at = now
        doc.save(update_fields=["status", "error_message", "processed_at"])
        return False

    finally:
        _delete_file(doc)


def _delete_file(doc: OCRJobDocument) -> None:
    """Borra el archivo físico del documento y limpia el campo en la BD."""
    if not doc.archivo or not doc.archivo.name:
        return
    try:
        storage = doc.archivo.storage
        name = doc.archivo.name
        if storage.exists(name):
            storage.delete(name)
        doc.archivo = ""
        doc.save(update_fields=["archivo"])
    except Exception as exc:
        logger.warning("[ocr] No se pudo borrar archivo del doc %s: %s", doc.id, exc)


def process_ocr_job(job: OCRJob) -> None:
    """Procesa todos los documentos del job. Continúa ante fallos individuales."""
    documents = list(job.documents.filter(status=OCRJobDocument.Status.PENDING))

    failed_count = 0
    for doc in documents:
        success = _process_document(doc)
        if not success:
            failed_count += 1

        job.processed_documents = models.F("processed_documents") + 1
        job.failed_documents = models.F("failed_documents") + (0 if success else 1)
        job.last_activity_at = timezone.now()
        job.save(
            update_fields=["processed_documents", "failed_documents", "last_activity_at"]
        )
        job.refresh_from_db(
            fields=["processed_documents", "failed_documents", "last_activity_at"]
        )

    now = timezone.now()
    if failed_count > 0:
        job.status = OCRJob.Status.COMPLETED_WITH_ERRORS
    else:
        job.status = OCRJob.Status.COMPLETED
    job.finished_at = now
    job.last_activity_at = now
    job.save(update_fields=["status", "finished_at", "last_activity_at"])


def process_next_ocr_job() -> bool:
    """
    Intenta procesar el próximo job pendiente.
    Retorna True si procesó un job (continuar de inmediato), False si no había ninguno.
    """
    mark_stale_ocr_jobs_as_failed()

    job = claim_next_ocr_job()
    if job is None:
        return False

    logger.info("[ocr] Procesando lote OCR #%s...", job.id)
    try:
        process_ocr_job(job)
        logger.info("[ocr] Lote OCR #%s finalizado con estado '%s'.", job.id, job.status)
    except Exception as exc:
        logger.exception("[ocr] Error inesperado en lote OCR #%s: %s", job.id, exc)
        OCRJob.objects.filter(pk=job.pk).update(
            status=OCRJob.Status.FAILED,
            last_error_message=str(exc),
            finished_at=timezone.now(),
        )

    return True


def run_ocr_jobs_worker(once: bool = False) -> None:
    """Loop principal del worker OCR."""
    logger.info("[ocr] Worker OCR iniciado.")
    poll_seconds = get_ocr_job_poll_seconds()

    while True:
        try:
            did_work = process_next_ocr_job()
        except Exception as exc:
            logger.exception("[ocr] Error inesperado en el worker OCR: %s", exc)
            did_work = False

        if once:
            break

        if not did_work:
            time.sleep(poll_seconds)
