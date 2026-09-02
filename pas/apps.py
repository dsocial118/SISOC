from django.apps import AppConfig


class PasConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "pas"
    verbose_name = "PAS"

    def ready(self):
        from pas.favorite_filters import (  # pylint: disable=import-outside-toplevel
            registrar_filtros_favoritos,
        )

        registrar_filtros_favoritos()
