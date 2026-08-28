from django.apps import AppConfig
from django.conf import settings


class DispositivosConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "services.dispositivos.monolith_compat.app"
    label = "dispositivos"

    def ready(self):
        if not getattr(settings, "DISPOSITIVOS_REGISTER_FAVORITES", False):
            return
        from .runtime import register_favorite_filters  # pylint: disable=import-outside-toplevel

        register_favorite_filters()
