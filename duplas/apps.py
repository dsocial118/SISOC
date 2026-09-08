from django.apps import AppConfig


class DuplaConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "duplas"

    def ready(self):
        """Importar signals cuando la app esté lista."""
        import duplas.signals  # noqa: F401  # pylint: disable=import-outside-toplevel,unused-import
        from duplas.favorite_filters import (  # pylint: disable=import-outside-toplevel
            registrar_filtros_favoritos,
        )

        registrar_filtros_favoritos()
        from duplas.user_form_catalog import (  # pylint: disable=import-outside-toplevel
            registrar_user_form_catalog,
        )

        registrar_user_form_catalog()
