import os
import threading
import logging
from concurrent.futures import ThreadPoolExecutor
import requests
from django.conf import settings
from django.db import close_old_connections
from django.utils import timezone

from relevamientos.models import Relevamiento


logger = logging.getLogger("django")
TIMEOUT = 360  # Segundos máximos de espera por respuesta


# Pool global para limitar la concurrencia de tareas asincrónicas
MAX_WORKERS = int(
    os.getenv("GESTIONAR_RELEVAMIENTOS_WORKERS", os.getenv("GESTIONAR_WORKERS", "2"))
)
_EXECUTOR = ThreadPoolExecutor(max_workers=MAX_WORKERS)


def _is_gestionar_integration_enabled() -> bool:
    return bool(getattr(settings, "GESTIONAR_INTEGRATION_ENABLED", False))


def _run_async_threads():
    """
    Permite desactivar hilos reales durante tests para evitar flakiness.
    """
    if os.getenv("DISABLE_ASYNC_THREADS", "false").lower() == "true":
        return False
    if os.getenv("PYTEST_CURRENT_TEST"):
        return False
    return True


def build_relevamiento_payload(relevamiento):
    fecha = (
        relevamiento.fecha_visita.strftime("%Y-%m-%d")
        if relevamiento.fecha_visita
        else timezone.now().strftime("%Y-%m-%d")
    )
    return {
        "Action": "Add",
        "Properties": {"Locale": "es-ES"},
        "Rows": [
            {
                "Relevamiento id": f"{relevamiento.id}",
                "Id_SISOC": f"{relevamiento.id}",
                "ESTADO": relevamiento.estado,
                "TecnicoRelevador": (
                    f"{relevamiento.territorial_uid}"
                    if relevamiento.territorial_uid
                    else ""
                ),
                "Fecha de visita": fecha,
                "Id_Comedor": f"{relevamiento.comedor_id}",
            }
        ],
    }


class AsyncSendRelevamientoToGestionar(threading.Thread):
    """Hilo para enviar relevamiento a GESTIONAR asincronamente"""

    def __init__(self, relevamiento_id, payload=None):
        super().__init__()
        self.relevamiento_id = relevamiento_id
        self.payload = payload

    def start(self):  # type: ignore[override]
        if not _is_gestionar_integration_enabled():
            logger.info(
                "Integración con GESTIONAR deshabilitada: se omite sync de relevamiento"
            )
            return None
        # Encola la ejecución en un pool limitado para evitar demasiadas conexiones
        if _run_async_threads():
            _EXECUTOR.submit(self.run)
            return None
        self.run()
        return None

    def run(self):
        if not _is_gestionar_integration_enabled():
            return
        # Asegura estado sano de conexiones en hilos de pool reutilizables
        close_old_connections()
        data = self.payload
        try:
            if data is None:
                relevamiento = Relevamiento.objects.get(id=self.relevamiento_id)
                data = build_relevamiento_payload(relevamiento)

            headers = {
                "applicationAccessKey": os.getenv("GESTIONAR_API_KEY"),
            }

            response = requests.post(
                os.getenv("GESTIONAR_API_CREAR_RELEVAMIENTO"),
                json=data,
                headers=headers,
                timeout=TIMEOUT,
            )
            response.raise_for_status()
            response_data = response.json()
            logger.info(
                f"RELEVAMIENTO {self.relevamiento_id} sincronizado con GESTIONAR con exito"
            )
            gestionar_pdf = response_data["Rows"][0].get("docPDF", "")
            if gestionar_pdf:
                # El .update() en el queryset es para evitar que salten las signals
                Relevamiento.objects.filter(pk=self.relevamiento_id).update(
                    docPDF=gestionar_pdf
                )

        except Exception:
            logger.exception(
                "Error al sincronizar RELEVAMIENTO con GESTIONAR",
                extra={
                    "relevamiento_pk": self.relevamiento_id,
                    "body": data,
                },
            )
        finally:
            # Cierra conexiones viejas tras finalizar el trabajo del hilo
            close_old_connections()


class AsyncRemoveRelevamientoToGestionar(threading.Thread):
    """Hilo para eliminar relevamiento de GESTIONAR asincronamente"""

    def __init__(self, relevamiento_id):
        super().__init__()
        self.relevamiento_id = relevamiento_id

    def start(self):  # type: ignore[override]
        if not _is_gestionar_integration_enabled():
            logger.info(
                "Integración con GESTIONAR deshabilitada: se omite baja de relevamiento"
            )
            return None
        if _run_async_threads():
            _EXECUTOR.submit(self.run)
            return None
        self.run()
        return None

    def run(self):
        if not _is_gestionar_integration_enabled():
            return
        close_old_connections()
        data = {
            "Action": "Delete",
            "Properties": {"Locale": "es-ES"},
            "Rows": [{"Relevamiento id": f"{self.relevamiento_id}"}],
        }
        headers = {
            "applicationAccessKey": os.getenv("GESTIONAR_API_KEY"),
        }

        try:
            response = requests.post(
                os.getenv("GESTIONAR_API_BORRAR_RELEVAMIENTO"),
                json=data,
                headers=headers,
                timeout=TIMEOUT,
            )
            response.raise_for_status()
            logger.info(
                f"RELEVAMIENTO {self.relevamiento_id} sincronizado con GESTIONAR con exito"
            )
        except Exception:
            logger.exception(
                "Error al sincronizar RELEVAMIENTO con GESTIONAR",
                extra={"relevamiento_pk": self.relevamiento_id, "body": data},
            )
        finally:
            close_old_connections()
