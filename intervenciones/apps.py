from django.apps import AppConfig


class IntervencionesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "intervenciones"

    def ready(self):
        import intervenciones.audit_signals  # pylint: disable=unused-import, import-outside-toplevel
        import intervenciones.signals  # pylint: disable=unused-import, import-outside-toplevel
        from intervenciones.fixture_post_load import (  # pylint: disable=import-outside-toplevel
            registrar_fixture_post_load_handler,
        )

        registrar_fixture_post_load_handler()
