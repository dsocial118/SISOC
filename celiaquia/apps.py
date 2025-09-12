from django.apps import AppConfig


class CeliaquiaConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "celiaquia"

    def ready(self):  # pragma: no cover - Django startup
        from . import signals  # pylint: disable=import-outside-toplevel, unused-import
