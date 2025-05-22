from django.apps import AppConfig


class HistorialConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "historial"

    def ready(self):
        import historial.signals  # pylint: disable=unused-import, import-outside-toplevel
