from django.apps import AppConfig


class DashboardConfig(AppConfig):
    name = "dashboard"

    def ready(self):
        from dashboard.signals import (  # pylint: disable=import-outside-toplevel
            register_signals,
        )

        register_signals()
