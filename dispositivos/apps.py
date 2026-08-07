from django.apps import AppConfig


class DispositivosConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "dispositivos"

    def ready(self):
        from dispositivos.favorite_filters import (  # pylint: disable=import-outside-toplevel
            registrar_filtros_favoritos,
        )

        registrar_filtros_favoritos()
