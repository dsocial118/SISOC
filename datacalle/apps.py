from django.apps import AppConfig


class DatacalleConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "datacalle"
    verbose_name = "DataCalle - Situación de Calle"

    def ready(self):
        from datacalle.sidebar_access import (  # pylint: disable=import-outside-toplevel
            registrar_acceso_sidebar,
        )

        registrar_acceso_sidebar()
