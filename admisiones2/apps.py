from django.apps import AppConfig


class AdmisionesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "admisiones2"

    def ready(self):
        import admisiones2.signals  # pylint: disable=unused-import, import-outside-toplevel
