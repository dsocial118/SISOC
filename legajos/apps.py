from django.apps import AppConfig


class LegajoConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "legajos"

    def ready(self):
        import legajos.signals  # pylint: disable=unused-import, import-outside-toplevel
