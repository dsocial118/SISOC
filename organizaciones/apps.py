from django.apps import AppConfig


class OrganizacionesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "organizaciones"

    def ready(self):
        from organizaciones.user_form_catalog import (  # pylint: disable=import-outside-toplevel
            registrar_user_form_catalog,
        )

        registrar_user_form_catalog()
