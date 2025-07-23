import os
import threading
import requests
from comedores.models import Comedor, Observacion, Referente
import os

TIMEOUT = 360  # Segundos máximos de espera por respuesta


def build_comedor_payload(comedor):
    fk = (
        lambda obj, attr, sub="nombre": getattr(getattr(obj, attr, None), sub, "") or ""
    )
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

    def run(self):
        headers = {"applicationAccessKey": os.getenv("GESTIONAR_API_KEY")}
        url = os.getenv("GESTIONAR_API_CREAR_COMEDOR")
        try:
            r = requests.post(url, json=self.payload, headers=headers, timeout=TIMEOUT)
            r.raise_for_status()
            print("COMEDOR sync OK")
        except Exception as e:
            print("!!! Error sync COMEDOR:", e, "\nBody:", self.payload)


class AsyncRemoveComedorToGestionar(threading.Thread):
    """Hilo para eliminar comedor a GESTIONAR asincronamente"""

    def __init__(self, comedor_id):
        super().__init__()
        self.comedor_id = comedor_id

    def run(self):
        comedor = Comedor.objects.get(id=self.comedor_id)
        data = {
            "Action": "Delete",
            "Properties": {"Locale": "es-ES"},
            "Rows": [{"ComedorID": f"{comedor.id}"}],
        }

        headers = {
            "applicationAccessKey": os.getenv("GESTIONAR_API_KEY"),
        }

        try:
            response = requests.post(
                os.getenv("GESTIONAR_API_BORRAR_COMEDOR"),
                json=data,
                headers=headers,
                timeout=TIMEOUT,
            )
            response.raise_for_status()
            print(f"COMEDOR {comedor.id} sincronizado con exito")
        except requests.exceptions.RequestException as e:
            print("!!! Error al sincronizar eliminacion de COMEDOR con GESTIONAR:")
            print(e)
            print("!!! Con el body:")
            print(data)


class AsyncSendReferenteToGestionar(threading.Thread):
    """Hilo para enviar referente a GESTIONAR asincronamente"""

    def __init__(self, referente_id):
        super().__init__()
        self.referente_id = referente_id

    def run(self):
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

        try:
            if referente.documento is not None:
                response = requests.post(
                    os.getenv("GESTIONAR_API_CREAR_REFERENTE"),
                    json=data,
                    headers=headers,
                    timeout=TIMEOUT,
                )
                response.raise_for_status()
                response = response.json()
                print(f"REFERENTE {referente.id} sincronizado con GESTIONAR con exito")

        except Exception as e:
            print("!!! Error al sincronizar REFERENTE con GESTIONAR:")
            print(e)
            print("!!! Con el body:")
            print(data)


class AsyncSendObservacionToGestionar(threading.Thread):
    """Hilo para enviar observacion a GESTIONAR asincronamente"""

    def __init__(self, observacion_id):
        super().__init__()
        self.observacion_id = observacion_id

    def run(self):
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
                    "FechaHora": observacion.fecha_visita.strftime("%d/%m/%Y %H:%M"),
                }
            ],
        }

        headers = {
            "applicationAccessKey": os.getenv("GESTIONAR_API_KEY"),
        }

        try:
            response = requests.post(
                os.getenv("GESTIONAR_API_CREAR_OBSERVACION"),
                json=data,
                headers=headers,
                timeout=TIMEOUT,
            )
            response.raise_for_status()
            response = response.json()
            print(f"OBSERVACION {observacion.id} sincronizada con exito")
        except Exception as e:
            print("!!! Error al sincronizar OBSERVACION con GESTIONAR:")
            print(e)
            print("!!! Con el body:")
            print(data)
