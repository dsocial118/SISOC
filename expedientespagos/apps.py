from django.apps import AppConfig


class ExpedientespagosConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "expedientespagos"

    def ready(self):
        import expedientespagos.signals  # pylint: disable=unused-import, import-outside-toplevel
