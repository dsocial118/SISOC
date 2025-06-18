from django.apps import AppConfig


class RelevamientosConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "relevamientos"

    def ready(self):
        import relevamientos.signals  # pylint: disable=unused-import, import-outside-toplevel
