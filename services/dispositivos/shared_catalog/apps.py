from django.apps import AppConfig


class SharedCatalogConfig(AppConfig):
    """Lectura mínima del catálogo legado mientras las FKs se preservan."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "services.dispositivos.shared_catalog"
    label = "core"
