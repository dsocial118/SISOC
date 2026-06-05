import os
import threading
import logging
from concurrent.futures import ThreadPoolExecutor
import requests
from django.conf import settings
from django.db import close_old_connections
from django.utils import timezone

from relevamientos.models import PrimerSeguimiento, Relevamiento


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


def build_primer_seguimiento_payload(seguimiento):
    # IMPORTANTE: el alta SOLO debe mandar Id_Relevamiento. En la tabla AppSheet
    # `Seguimientos1erVisita`, `ID_Seguimiento1` es la CLAVE autogenerada: si el
    # payload la incluye, AppSheet rechaza el alta en silencio (responde 200 con
    # cuerpo vacio y no crea la fila). GESTIONAR genera el `ID_Seguimiento1` y lo
    # devuelve en la respuesta; SISOC lo persiste en `gestionar_id`. `Id_SISOC` no
    # es columna de esa tabla. Verificado contra la API real el 2026-06-04.
    return {
        "Action": "Add",
        "Properties": {"Locale": "es-ES"},
        "Rows": [
            {
                "Id_Relevamiento": f"{seguimiento.id_relevamiento_id}",
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
            response_data = response.json() if response.content else {}
            rows = response_data.get("Rows") or []
            if not rows:
                logger.warning(
                    "RELEVAMIENTO %s: GESTIONAR respondio 2xx pero no devolvio filas; "
                    "la alta podria no haberse registrado. Respuesta: %s",
                    self.relevamiento_id,
                    response_data,
                )
                return
            # GESTIONAR confirmo la fila: marcamos sincronizado (mas el docPDF si
            # lo devolvio). El .update() en el queryset evita disparar signals.
            campos_sync = {"sincronizado_gestionar": True}
            gestionar_pdf = rows[0].get("docPDF", "")
            if gestionar_pdf:
                campos_sync["docPDF"] = gestionar_pdf
            Relevamiento.objects.filter(pk=self.relevamiento_id).update(**campos_sync)
            logger.info(
                "RELEVAMIENTO %s sincronizado con GESTIONAR con exito",
                self.relevamiento_id,
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


class AsyncSendPrimerSeguimientoToGestionar(threading.Thread):
    """Hilo para enviar primer seguimiento a GESTIONAR asincronamente"""

    def __init__(self, seguimiento_id, payload=None):
        super().__init__()
        self.seguimiento_id = seguimiento_id
        self.payload = payload

    def start(self):  # type: ignore[override]
        if not _is_gestionar_integration_enabled():
            logger.info(
                "Integracion con GESTIONAR deshabilitada: "
                "se omite sync de primer seguimiento"
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
        data = self.payload
        try:
            if data is None:
                seguimiento = PrimerSeguimiento.objects.select_related(
                    "id_relevamiento__comedor"
                ).get(id=self.seguimiento_id)
                data = build_primer_seguimiento_payload(seguimiento)

            headers = {
                "applicationAccessKey": os.getenv("GESTIONAR_API_KEY"),
            }

            response = requests.post(
                os.getenv("GESTIONAR_API_CREAR_PRIMER_SEGUIMIENTO"),
                json=data,
                headers=headers,
                timeout=TIMEOUT,
            )
            response.raise_for_status()
            response_data = response.json() if response.content else {}
            rows = response_data.get("Rows") or []
            if not rows:
                # AppSheet responde 200 aunque rechace el alta (p. ej. el
                # Id_Relevamiento apunta a un relevamiento que GESTIONAR no tiene,
                # o falta una columna requerida de la tabla): en esos casos no
                # devuelve filas. No marcamos sincronizado para no mostrar un
                # estado enganoso, y dejamos el cuerpo en el log para diagnostico.
                logger.warning(
                    "PRIMER SEGUIMIENTO %s: GESTIONAR respondio 2xx pero no devolvio "
                    "filas; la alta podria no haberse registrado. Respuesta: %s",
                    self.seguimiento_id,
                    response_data,
                )
                return
            # GESTIONAR confirmo la fila: marcamos sincronizado (mas el
            # gestionar_id si lo devolvio). El PATCH entrante con los bloques
            # completos lo mantiene en True.
            gestionar_id = (rows[0].get("ID_Seguimiento1") or "").strip()
            campos_sync = {"sincronizado_gestionar": True}
            if gestionar_id:
                campos_sync["gestionar_id"] = gestionar_id
            PrimerSeguimiento.objects.filter(pk=self.seguimiento_id).update(
                **campos_sync
            )
            logger.info(
                "PRIMER SEGUIMIENTO %s sincronizado con GESTIONAR con exito",
                self.seguimiento_id,
            )
        except Exception:
            logger.exception(
                "Error al sincronizar PRIMER SEGUIMIENTO con GESTIONAR",
                extra={"primer_seguimiento_pk": self.seguimiento_id, "body": data},
            )
        finally:
            close_old_connections()


class AsyncRemovePrimerSeguimientoToGestionar(threading.Thread):
    """Hilo para eliminar primer seguimiento de GESTIONAR asincronamente"""

    def __init__(self, seguimiento_id, gestionar_id, relevamiento_id=None):
        super().__init__()
        self.seguimiento_id = seguimiento_id
        self.gestionar_id = gestionar_id
        self.relevamiento_id = relevamiento_id

    def start(self):  # type: ignore[override]
        if not _is_gestionar_integration_enabled():
            logger.info(
                "Integracion con GESTIONAR deshabilitada: "
                "se omite baja de primer seguimiento"
            )
            return None
        if not self.gestionar_id:
            logger.info(
                "Primer seguimiento %s sin gestionar_id: se omite baja",
                self.seguimiento_id,
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
        # La tabla `Seguimientos1erVisita` tiene CLAVE COMPUESTA
        # (ID_Seguimiento1 + Id_Relevamiento): el Delete debe informar ambos o
        # AppSheet responde 400 "Row key field 'Id_Relevamiento' value is missing".
        data = {
            "Action": "Delete",
            "Properties": {"Locale": "es-ES"},
            "Rows": [
                {
                    "ID_Seguimiento1": f"{self.gestionar_id}",
                    "Id_Relevamiento": f"{self.relevamiento_id}",
                }
            ],
        }
        headers = {
            "applicationAccessKey": os.getenv("GESTIONAR_API_KEY"),
        }

        try:
            response = requests.post(
                os.getenv("GESTIONAR_API_BORRAR_PRIMER_SEGUIMIENTO"),
                json=data,
                headers=headers,
                timeout=TIMEOUT,
            )
            response.raise_for_status()
            logger.info(
                "PRIMER SEGUIMIENTO %s eliminado en GESTIONAR con exito",
                self.seguimiento_id,
            )
        except Exception:
            logger.exception(
                "Error al eliminar PRIMER SEGUIMIENTO en GESTIONAR",
                extra={"primer_seguimiento_pk": self.seguimiento_id, "body": data},
            )
        finally:
            close_old_connections()
