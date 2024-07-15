from django.apps import AppConfig


class DashboardConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Dashboard'

    def ready(self):
        import Dashboard.signals