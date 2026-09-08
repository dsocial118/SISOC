from django.apps import AppConfig


class RendicioncuentasmensualConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "rendicioncuentasmensual"

    def ready(self):
        from rendicioncuentasmensual.favorite_filters import (  # pylint: disable=import-outside-toplevel
            registrar_filtros_favoritos,
        )

        registrar_filtros_favoritos()
