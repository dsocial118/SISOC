import os
import threading
import logging
from concurrent.futures import ThreadPoolExecutor
import requests
from django.db import close_old_connections
from django.utils import timezone

from relevamientos.models import Relevamiento


logger = logging.getLogger("django")
TIMEOUT = 360  # Segundos máximos de espera por respuesta


# Pool global para limitar la concurrencia de tareas asincrónicas
MAX_WORKERS = int(os.getenv("GESTIONAR_WORKERS", "5"))
_EXECUTOR = ThreadPoolExecutor(max_workers=MAX_WORKERS)


# FIXME: Evitar que se ejecute el hilo al correr los tests
class AsyncSendRelevamientoToGestionar(threading.Thread):
    """Hilo para enviar relevamiento a GESTIONAR asincronamente"""

    def __init__(self, relevamiento_id):
        super().__init__()
        self.relevamiento_id = relevamiento_id

    def start(self):  # type: ignore[override]
        # Encola la ejecución en un pool limitado para evitar demasiadas conexiones
        _EXECUTOR.submit(self.run)

    def run(self):
        # Asegura estado sano de conexiones en hilos de pool reutilizables
        close_old_connections()
        relevamiento = Relevamiento.objects.get(id=self.relevamiento_id)

        fecha_visita = relevamiento.fecha_visita or timezone.now()
        if timezone.is_naive(fecha_visita):
            fecha_visita = timezone.make_aware(
                fecha_visita, timezone.get_current_timezone()
            )
        fecha_visita_str = fecha_visita.astimezone(timezone.get_current_timezone()).strftime(
            "%d/%m/%Y %H:%M"
        )

        data = {
            "Action": "Add",
            "Properties": {"Locale": "es-ES"},
            "Rows": [
                {
                    "Relevamiento id": f"{relevamiento.id}",
                    "Id_SISOC": f"{relevamiento.id}",
                    "ESTADO": relevamiento.estado or "",
                    "TecnicoRelevador": (
                        f"{relevamiento.territorial_uid}"
                        if relevamiento.territorial_uid
                        else ""
                    ),
                    "Fecha de visita": fecha_visita_str,
                    "Id_Comedor": f"{relevamiento.comedor.id}",
                }
            ],
        }

        headers = {
            "applicationAccessKey": os.getenv("GESTIONAR_API_KEY"),
        }

        try:
            response = requests.post(
                os.getenv("GESTIONAR_API_CREAR_RELEVAMIENTO"),
                json=data,
                headers=headers,
                timeout=TIMEOUT,
            )
            response.raise_for_status()
            response_data = response.json()
            logger.info(
                f"RELEVAMIENTO {relevamiento.id} sincronizado con GESTIONAR con exito"
            )
            gestionar_pdf = response_data["Rows"][0].get("docPDF", "")
            if gestionar_pdf:
                # El .update() en el queryset es para evitar que salten las signals
                Relevamiento.objects.filter(pk=relevamiento.id).update(
                    docPDF=gestionar_pdf
                )

        except requests.HTTPError as exc:
            response_content = exc.response.text if exc.response is not None else ""
            logger.exception(
                "Error al sincronizar RELEVAMIENTO con GESTIONAR",
                extra={
                    "relevamiento_pk": relevamiento.id,
                    "body": data,
                    "status_code": exc.response.status_code if exc.response else None,
                    "response_text": response_content[:1000],
                },
            )
        except Exception:
            logger.exception(
                "Error al sincronizar RELEVAMIENTO con GESTIONAR",
                extra={"relevamiento_pk": relevamiento.id, "body": data},
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
        _EXECUTOR.submit(self.run)

    def run(self):
        close_old_connections()
        relevamiento = Relevamiento.objects.get(id=self.relevamiento_id)

        data = {
            "Action": "Delete",
            "Properties": {"Locale": "es-ES"},
            "Rows": [{"Relevamiento id": f"{relevamiento.id}"}],
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
                f"RELEVAMIENTO {relevamiento.id} sincronizado con GESTIONAR con exito"
            )
        except Exception:
            logger.exception(
                "Error al sincronizar RELEVAMIENTO con GESTIONAR",
                extra={"relevamiento_pk": relevamiento.id, "body": data},
            )
        finally:
            close_old_connections()
