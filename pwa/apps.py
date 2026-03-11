from django.apps import AppConfig
from django.db.models.signals import post_migrate


class PwaConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "pwa"

    def ready(self):
        from pwa.signals import seed_catalogo_actividades  # pylint: disable=import-outside-toplevel

        post_migrate.connect(
            seed_catalogo_actividades,
            sender=self,
            dispatch_uid="pwa.bootstrap_catalogo",
        )
