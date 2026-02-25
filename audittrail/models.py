"""Modelos auxiliares de auditoría propios de SISOC."""

from django.db import models


class AuditEntryMeta(models.Model):
    """
    Metadata complementaria para `auditlog.LogEntry`.

    Se almacena fuera de django-auditlog para mantener compatibilidad con la
    librería y permitir evolucionar trazabilidad (batch/source/snapshots) sin
    tocar el esquema de terceros.
    """

    log_entry = models.OneToOneField(
        "auditlog.LogEntry",
        on_delete=models.CASCADE,
        related_name="audittrail_meta",
    )
    actor_username_snapshot = models.CharField(max_length=150, blank=True, default="")
    actor_full_name_snapshot = models.CharField(max_length=255, blank=True, default="")
    actor_display_snapshot = models.CharField(max_length=255, blank=True, default="")
    source = models.CharField(max_length=64, blank=True, default="", db_index=True)
    batch_key = models.CharField(max_length=255, blank=True, default="", db_index=True)
    extra = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Metadata de auditoría"
        verbose_name_plural = "Metadatas de auditoría"
        permissions = (
            ("export_auditlog", "Puede exportar resultados de auditoría"),
        )

    def __str__(self):
        return f"AuditEntryMeta(log_entry_id={self.log_entry_id})"
