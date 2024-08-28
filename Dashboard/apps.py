from django.apps import AppConfig


class DashboardConfig(AppConfig):
    name = "Dashboard"

    def ready(self):
        from Dashboard import signals

        signals.register_signals()
