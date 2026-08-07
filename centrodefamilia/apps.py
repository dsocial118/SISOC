from django.apps import AppConfig


class CentrodefamiliaConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "centrodefamilia"

    def ready(self):
        from centrodefamilia.services.consulta_renaper import (  # pylint: disable=import-outside-toplevel
            consultar_datos_renaper,
        )
        from centrodefamilia.favorite_filters import (  # pylint: disable=import-outside-toplevel
            registrar_filtros_favoritos,
        )
        from core.services.renaper import (  # pylint: disable=import-outside-toplevel
            registrar_consulta_renaper,
        )

        registrar_filtros_favoritos()
        registrar_consulta_renaper(consultar_datos_renaper)
        from centrodefamilia.ciudadano_detail import (  # pylint: disable=import-outside-toplevel
            registrar_contribucion_ciudadano,
        )

        registrar_contribucion_ciudadano()
