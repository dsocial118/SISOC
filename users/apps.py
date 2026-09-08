from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "users"

    def ready(self):
        """Importar signals cuando la app esté lista."""
        import users.signals  # noqa: F401  # pylint: disable=import-outside-toplevel,unused-import
        from users.favorite_filters import (  # pylint: disable=import-outside-toplevel
            registrar_filtros_favoritos,
        )

        registrar_filtros_favoritos()
