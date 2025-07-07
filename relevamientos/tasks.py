import os
import threading
import logging
import requests
from django.utils import timezone
from relevamientos.models import Relevamiento


logger = logging.getLogger(__name__)
TIMEOUT = 360  # Segundos máximos de espera por respuesta


# FIXME: Evitar que se ejecute el hilo al correr los tests
class AsyncSendRelevamientoToGestionar(threading.Thread):
    """Hilo para enviar relevamiento a GESTIONAR asincronamente"""

    def __init__(self, relevamiento_id):
        super().__init__()
        self.relevamiento_id = relevamiento_id

    def run(self):
        relevamiento = Relevamiento.objects.get(id=self.relevamiento_id)

        data = {
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
                    "Fecha de visita": (
                        relevamiento.fecha_visita.strftime("%Y-%m-%d")
                        if relevamiento.fecha_visita
                        else timezone.now().strftime("%Y-%m-%d")
                    ),
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

        except Exception as e:
            logger.error(
                f"Error al sincronizar RELEVAMIENTO {relevamiento.id} con GESTIONAR: {e}"
            )
            logger.error(f"Con el body: {data}")


class AsyncRemoveRelevamientoToGestionar(threading.Thread):
    """Hilo para eliminar relevamiento de GESTIONAR asincronamente"""

    def __init__(self, relevamiento_id):
        super().__init__()
        self.relevamiento_id = relevamiento_id

    def run(self):
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
        except Exception as e:
            logger.error(
                f"Error al sincronizar RELEVAMIENTO {relevamiento.id} con GESTIONAR: {e}"
            )
            logger.error(f"Con el body: {data}")
