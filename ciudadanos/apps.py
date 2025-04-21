from django.apps import AppConfig


class CiudadanoConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "ciudadanos"

    def ready(self):
        import ciudadanos.signals  # pylint: disable=unused-import, import-outside-toplevel
