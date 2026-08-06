from django.apps import AppConfig


class AdmisionesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "admisiones"

    def ready(self):
        import admisiones.signals  # pylint: disable=unused-import, import-outside-toplevel
        from admisiones.favorite_filters import (  # pylint: disable=import-outside-toplevel
            registrar_filtros_favoritos,
        )

        registrar_filtros_favoritos()
