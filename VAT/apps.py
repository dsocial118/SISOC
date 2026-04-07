from django.apps import AppConfig


class VATConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "VAT"

    def ready(self):
        import VAT.cache_utils  # noqa: F401, pylint: disable=import-outside-toplevel,unused-import
