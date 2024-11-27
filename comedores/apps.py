from django.apps import AppConfig


class ComedoresConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "comedores"

    def ready(self):
        import comedores.signals  # pylint: disable=unused-import, import-outside-toplevel
