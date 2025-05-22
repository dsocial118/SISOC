import atexit
from concurrent.futures import ThreadPoolExecutor
from django.apps import AppConfig


class HistorialConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "historial"

    def ready(self):
        import historial.signals  # pylint: disable=unused-import
        from historial import async_handlers  # pylint: disable=import-outside-toplevel

        async_handlers.executor = ThreadPoolExecutor(max_workers=5)
        atexit.register(async_handlers.executor.shutdown, wait=False)
