from django.apps import AppConfig


class IntervencionesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "intervenciones"

    def ready(self):
        import intervenciones.signals  # pylint: disable=unused-import, import-outside-toplevel
