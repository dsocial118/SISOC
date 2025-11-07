from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "users"

    def ready(self):
        """Importar signals cuando la app esté lista."""
        import users.signals  # noqa: F401
