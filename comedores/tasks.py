import os
import logging
import threading
from concurrent.futures import ThreadPoolExecutor

import requests
from django.db import close_old_connections

from comedores.models import Comedor, Observacion, Referente

TIMEOUT = 360  # Segundos máximos de espera por respuesta
MAX_WORKERS = int(
    os.getenv("GESTIONAR_COMEDORES_WORKERS", os.getenv("GESTIONAR_WORKERS", "5"))
)
_EXECUTOR = ThreadPoolExecutor(max_workers=MAX_WORKERS)

logger = logging.getLogger("django")


def build_comedor_payload(comedor):

    def fk(obj, attr, sub="nombre"):
        return getattr(getattr(obj, attr, None), sub, "") or ""

    return {
        "Action": "Add",
        "Properties": {"Locale": "es-ES"},
        "Rows": [
            {
                "ComedorID": comedor.id,
                "ID_Sisoc": comedor.id,
                "nombre": comedor.nombre or "",
                "comienzo": (
                    f"01/01/{comedor.comienzo}" if comedor.comienzo else "01/01/1900"
                ),
                "TipoComedor": fk(comedor, "tipocomedor"),
                "calle": comedor.calle or "",
                "numero": comedor.numero or "",
                "entre_calle_1": comedor.entre_calle_1 or "",
                "entre_calle_2": comedor.entre_calle_2 or "",
                "provincia": fk(comedor, "provincia"),
                "municipio": fk(comedor, "municipio"),
                "localidad": fk(comedor, "localidad"),
                "partido": comedor.partido or "",
                "barrio": comedor.barrio or "",
                "lote": comedor.lote or "",
                "manzana": comedor.manzana or "",
                "piso": comedor.piso or "",
                "longitud": comedor.longitud or "",
                "latitud": comedor.latitud or "",
                "programa": fk(comedor, "programa"),
                "Organizacion": fk(comedor, "organizacion"),
                "departamento": comedor.departamento or "",
                "codigo_postal": comedor.codigo_postal or "",
                "Referente": getattr(
                    getattr(comedor, "referente", None), "documento", ""
                )
                or "",
                "Imagen": (
                    f"{os.getenv('DOMINIO')}/media/{comedor.foto_legajo}"
                    if comedor.foto_legajo
                    else ""
                ),
            }
        ],
    }


class AsyncSendComedorToGestionar(threading.Thread):
    def __init__(self, payload):
        super().__init__(daemon=True)
        self.payload = payload

    def start(self):  # type: ignore[override]
        _EXECUTOR.submit(self.run)

    def run(self):
        close_old_connections()
        headers = {"applicationAccessKey": os.getenv("GESTIONAR_API_KEY")}
        url = os.getenv("GESTIONAR_API_CREAR_COMEDOR")
        try:
            r = requests.post(url, json=self.payload, headers=headers, timeout=TIMEOUT)
            r.raise_for_status()
            data = r.json()
            logger.info(
                f"COMEDOR {data['Rows'][0]['ComedorID']} sincronizado con exito"
            )
        except Exception:
            logger.exception(
                "Error al sincronizar COMEDOR con GESTIONAR",
                extra={"body": self.payload},
            )
        finally:
            close_old_connections()


class AsyncRemoveComedorToGestionar(threading.Thread):
    """Hilo para eliminar comedor a GESTIONAR asincronamente"""

    def __init__(self, comedor_id):
        super().__init__()
        self.comedor_id = comedor_id

    def start(self):  # type: ignore[override]
        _EXECUTOR.submit(self.run)

    def run(self):
        close_old_connections()
        try:
            comedor = Comedor.objects.get(id=self.comedor_id)
            data = {
                "Action": "Delete",
                "Properties": {"Locale": "es-ES"},
                "Rows": [{"ComedorID": f"{comedor.id}"}],
            }

            headers = {
                "applicationAccessKey": os.getenv("GESTIONAR_API_KEY"),
            }

            response = requests.post(
                os.getenv("GESTIONAR_API_BORRAR_COMEDOR"),
                json=data,
                headers=headers,
                timeout=TIMEOUT,
            )
            response.raise_for_status()
            logger.info(f"COMEDOR {comedor.id} sincronizado con exito")
        except Exception:
            logger.exception(
                "Error al sincronizar eliminacion de COMEDOR con GESTIONAR",
                extra={"body": data},
            )
        finally:
            close_old_connections()


class AsyncSendReferenteToGestionar(threading.Thread):
    """Hilo para enviar referente a GESTIONAR asincronamente"""

    def __init__(self, referente_id):
        super().__init__()
        self.referente_id = referente_id

    def start(self):  # type: ignore[override]
        _EXECUTOR.submit(self.run)

    def run(self):
        close_old_connections()
        try:
            referente = Referente.objects.get(id=self.referente_id)

            data = {
                "Action": "Add",
                "Properties": {"Locale": "es-ES"},
                "Rows": [
                    {
                        "documento": referente.documento,
                        "nombre": referente.nombre,
                        "apellido": referente.apellido,
                        "mail": referente.mail,
                        "celular": referente.celular,
                    }
                ],
            }

            headers = {
                "applicationAccessKey": os.getenv("GESTIONAR_API_KEY"),
            }

            if referente.documento is not None:
                response = requests.post(
                    os.getenv("GESTIONAR_API_CREAR_REFERENTE"),
                    json=data,
                    headers=headers,
                    timeout=TIMEOUT,
                )
                response.raise_for_status()
                response = response.json()
                logger.info(
                    f"REFERENTE {referente.id} sincronizado con GESTIONAR con exito"
                )

        except Exception:
            logger.exception(
                "Error al sincronizar REFERENTE con GESTIONAR",
                extra={"body": data},
            )
        finally:
            close_old_connections()


class AsyncSendObservacionToGestionar(threading.Thread):
    """Hilo para enviar observacion a GESTIONAR asincronamente"""

    def __init__(self, observacion_id):
        super().__init__()
        self.observacion_id = observacion_id

    def start(self):  # type: ignore[override]
        _EXECUTOR.submit(self.run)

    def run(self):
        close_old_connections()
        try:
            observacion = Observacion.objects.get(id=self.observacion_id)

            data = {
                "Action": "Add",
                "Properties": {"Locale": "es-ES"},
                "Rows": [
                    {
                        "Comedor_Id": observacion.comedor.id,
                        "OBSERVACION": observacion.observacion,
                        "Adjunto": "",
                        "Usr": "",
                        "FechaHora": observacion.fecha_visita.strftime(
                            "%d/%m/%Y %H:%M"
                        ),
                    }
                ],
            }

            headers = {
                "applicationAccessKey": os.getenv("GESTIONAR_API_KEY"),
            }

            response = requests.post(
                os.getenv("GESTIONAR_API_CREAR_OBSERVACION"),
                json=data,
                headers=headers,
                timeout=TIMEOUT,
            )
            response.raise_for_status()
            response = response.json()
            logger.info(f"OBSERVACION {observacion.id} sincronizada con exito")
        except Exception:
            logger.exception(
                "Error al sincronizar OBSERVACION con GESTIONAR", extra={"body": data}
            )
        finally:
            close_old_connections()
