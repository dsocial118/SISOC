from django.apps import AppConfig


class ComedoresConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "comedores"

    def ready(self):
        import comedores.audit_signals  # pylint: disable=unused-import, import-outside-toplevel
        import comedores.signals  # pylint: disable=unused-import, import-outside-toplevel
        from comedores.favorite_filters import (  # pylint: disable=import-outside-toplevel
            registrar_filtros_favoritos,
        )

        registrar_filtros_favoritos()
        from comedores.ciudadano_detail import (  # pylint: disable=import-outside-toplevel
            registrar_contribucion_ciudadano,
        )

        registrar_contribucion_ciudadano()
        from comedores.pwa_capabilities import (  # pylint: disable=import-outside-toplevel
            registrar_capacidades_pwa,
        )

        registrar_capacidades_pwa()
        from comedores.user_form_catalog import (  # pylint: disable=import-outside-toplevel
            registrar_user_form_catalog,
        )

        registrar_user_form_catalog()
        from comedores.pwa_user_import import (  # pylint: disable=import-outside-toplevel
            registrar_resolvedor_user_import_pwa,
        )

        registrar_resolvedor_user_import_pwa()
