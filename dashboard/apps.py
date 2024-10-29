from django.apps import AppConfig


class DashboardConfig(AppConfig):
    name = "dashboard"

    def ready(self):
        from dashboard import signals  # pylint: disable=import-outside-toplevel

        signals.register_signals()
