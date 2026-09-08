from django.apps import AppConfig


class AcompanamientosConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "acompanamientos"

    def ready(self):
        from acompanamientos.favorite_filters import (  # pylint: disable=import-outside-toplevel
            registrar_filtros_favoritos,
        )

        registrar_filtros_favoritos()
