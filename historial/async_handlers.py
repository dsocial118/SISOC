from django.contrib.contenttypes.models import ContentType
from django.db import close_old_connections
from historial.models import Historial

# Esta variable se inicializa en el AppConfig
executor = None  # pylint: disable=invalid-name


def log_action_async(usuario, accion, instancia, diferencias):
    if executor is None:
        raise RuntimeError(
            "Executor no inicializado. Revisar el HistorialConfig.ready()"
        )

    def task():
        close_old_connections()
        Historial.objects.create(
            usuario=usuario,
            accion=accion,
            content_type=ContentType.objects.get_for_model(instancia),
            object_id=str(instancia.pk),
            diferencias=diferencias,
        )
        close_old_connections()

    executor.submit(task)
