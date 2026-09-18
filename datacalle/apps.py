from django.apps import AppConfig


class DatacalleConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "datacalle"
    verbose_name = "DataCalle - Situación de Calle"

    def ready(self):
        from auditlog.registry import (  # pylint: disable=import-outside-toplevel
            auditlog,
        )

        from datacalle.models import (  # pylint: disable=import-outside-toplevel
            Encuesta,
            Relevamiento,
        )
        from datacalle.sidebar_access import (  # pylint: disable=import-outside-toplevel
            registrar_acceso_sidebar,
        )

        # 8.6 del documento funcional: quien modifico el operativo y cuando.
        # `creado_por` y `cerrado_por` cubren las puntas; esto cubre el medio.
        auditlog.register(Relevamiento)
        auditlog.register(Encuesta)

        registrar_acceso_sidebar()
