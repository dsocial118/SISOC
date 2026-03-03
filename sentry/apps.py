from django.apps import AppConfig


class SentryConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "sentry"

    def ready(self):
        from sentry.services import initialize_sentry_sdk

        initialize_sentry_sdk()
