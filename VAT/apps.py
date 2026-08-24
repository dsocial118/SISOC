from django.apps import AppConfig


class VATConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "VAT"

    def ready(self):
        import VAT.cache_utils  # noqa: F401, pylint: disable=import-outside-toplevel,unused-import
        from VAT.favorite_filters import (  # pylint: disable=import-outside-toplevel
            registrar_filtros_favoritos,
        )
        from VAT.cache_utils import (  # pylint: disable=import-outside-toplevel
            invalidate_planes_centro_cache_on_soft_delete,
        )
        from VAT.sidebar_access import (  # pylint: disable=import-outside-toplevel
            registrar_acceso_sidebar,
        )
        from core.soft_delete.registry import (  # pylint: disable=import-outside-toplevel
            registrar_backfill_side_effect_handler,
        )

        registrar_filtros_favoritos()
        registrar_backfill_side_effect_handler(
            "VAT.invalidate_planes_centro_cache",
            invalidate_planes_centro_cache_on_soft_delete,
        )
        registrar_acceso_sidebar()
        from VAT.ciudadano_detail import (  # pylint: disable=import-outside-toplevel
            registrar_contribucion_ciudadano,
        )

        registrar_contribucion_ciudadano()
