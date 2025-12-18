from django.apps import AppConfig


class AudittrailConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "audittrail"
    verbose_name = "Auditoría"

    def ready(self):
        # Registro centralizado de modelos auditados.
        from audittrail.registry import register_tracked_models
        import audittrail.signals  # pylint: disable=unused-import, import-outside-toplevel

        register_tracked_models()
