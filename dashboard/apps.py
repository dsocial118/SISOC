from importlib import import_module

from django.apps import AppConfig


class DashboardConfig(AppConfig):
    name = "dashboard"

    def ready(self):
        import_module("dashboard.signals")
