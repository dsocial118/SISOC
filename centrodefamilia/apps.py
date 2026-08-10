from django.apps import AppConfig


class CentrodefamiliaConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "centrodefamilia"

    def ready(self):
        from centrodefamilia.favorite_filters import (  # pylint: disable=import-outside-toplevel
            registrar_filtros_favoritos,
        )

        registrar_filtros_favoritos()
        from centrodefamilia.ciudadano_detail import (  # pylint: disable=import-outside-toplevel
            registrar_contribucion_ciudadano,
        )

        registrar_contribucion_ciudadano()
