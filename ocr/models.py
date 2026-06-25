from __future__ import annotations

from django.conf import settings
from django.db import models


def ocr_document_upload_to(instance, filename):
    return f"ocr/jobs/{instance.job.requested_by_id}/{filename}"


class OCRJob(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pendiente"
        PROCESSING = "processing", "Procesando"
        COMPLETED = "completed", "Completado"
        COMPLETED_WITH_ERRORS = "completed_with_errors", "Completado con errores"
        FAILED = "failed", "Fallido"

    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.DO_NOTHING,
        related_name="ocr_jobs",
    )
    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    total_documents = models.PositiveIntegerField(default=0)
    processed_documents = models.PositiveIntegerField(default=0)
    failed_documents = models.PositiveIntegerField(default=0)
    last_error_message = models.TextField(blank=True)
    requested_at = models.DateTimeField(auto_now_add=True, db_index=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    last_activity_at = models.DateTimeField(null=True, blank=True, db_index=True)

    class Meta:
        ordering = ["-requested_at", "-id"]
        indexes = [
            models.Index(fields=["status", "requested_at"]),
            models.Index(fields=["requested_by", "requested_at"]),
        ]
        verbose_name = "Lote OCR"
        verbose_name_plural = "Lotes OCR"
        permissions = [
            ("use_ocr", "Puede usar el módulo OCR"),
        ]

    def __str__(self):
        return f"Lote OCR {self.id} ({self.get_status_display()})"


class OCRJobDocument(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pendiente"
        PROCESSING = "processing", "Procesando"
        COMPLETED = "completed", "Completado"
        NO_TEXT = "no_text", "Sin texto legible"
        FAILED = "failed", "Fallido"

    job = models.ForeignKey(
        OCRJob,
        on_delete=models.CASCADE,
        related_name="documents",
    )
    archivo = models.FileField(upload_to=ocr_document_upload_to, blank=True)
    original_filename = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField(null=True, blank=True)
    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    extracted_text = models.TextField(blank=True)
    page_count = models.PositiveIntegerField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["id"]
        indexes = [
            models.Index(fields=["job", "status"]),
        ]
        verbose_name = "Documento OCR"
        verbose_name_plural = "Documentos OCR"

    def __str__(self):
        return f"Doc {self.id} '{self.original_filename}' ({self.get_status_display()})"
