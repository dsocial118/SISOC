from django.apps import AppConfig


class DashboardConfig(AppConfig):
    name = "Dashboard"

    def ready(self):
        from dashboard import signals

        signals.register_signals()
