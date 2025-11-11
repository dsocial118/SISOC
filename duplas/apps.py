from django.apps import AppConfig


class DuplaConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "duplas"

    def ready(self):
        """Importar signals cuando la app esté lista."""
        import duplas.signals  # noqa: F401  # pylint: disable=import-outside-toplevel,unused-import
