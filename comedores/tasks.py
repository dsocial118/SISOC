import os
import threading
import requests
from comedores.models.comedor import Comedor, Observacion, Referente
from comedores.models.relevamiento import Relevamiento

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
                        else ""
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
            print(
                f"RELEVAMIENTO {relevamiento.id} sincronizado con GESTIONAR con exito"
            )

            gestionar_pdf = response_data["Rows"][0].get("docPDF", "")
            if gestionar_pdf:
                # El .update() en el queryset es para evitar que salten las signals
                Relevamiento.objects.filter(pk=relevamiento.id).update(
                    docPDF=gestionar_pdf
                )

        except Exception as e:
            print("!!! Error al sincronizar creacion de RELEVAMIENTO con GESTIONAR:")
            print(e)
            print("!!! Con el body:")
            print(data)


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
            print(
                f"RELEVAMIENTO {relevamiento.id} sincronizado con GESTIONAR con exito"
            )
        except Exception as e:
            print("!!! Error al sincronizar eliminacion de RELEVAMIENTO con GESTIONAR:")
            print(e)
            print("!!! Con el body:")
            print(data)


class AsyncSendComedorToGestionar(threading.Thread):
    """Hilo para enviar comedor a GESTIONAR asincronamente"""

    def __init__(self, comedor_id):
        super().__init__()
        self.comedor_id = comedor_id

    def run(self):
        comedor = Comedor.objects.get(id=self.comedor_id)

        data = {
            "Action": "Add",
            "Properties": {"Locale": "es-ES"},
            "Rows": [
                {
                    "ComedorID": comedor.id,
                    "ID_Sisoc": comedor.id,
                    "nombre": comedor.nombre,
                    "comienzo": (
                        f"01/01/{comedor.comienzo}"
                        if comedor.comienzo
                        else "01/01/1900"
                    ),
                    "TipoComedor": (
                        comedor.tipocomedor.nombre if comedor.tipocomedor else ""
                    ),
                    "calle": comedor.calle if comedor.calle else "",
                    "numero": comedor.numero if comedor.numero else "",
                    "entre_calle_1": (
                        comedor.entre_calle_1 if comedor.entre_calle_1 else ""
                    ),
                    "entre_calle_2": (
                        comedor.entre_calle_2 if comedor.entre_calle_2 else ""
                    ),
                    "provincia": (
                        comedor.provincia.nombre if comedor.provincia else ""
                    ),
                    "municipio": (
                        comedor.municipio.nombre if comedor.municipio else ""
                    ),
                    "localidad": (
                        comedor.localidad.nombre if comedor.localidad else ""
                    ),
                    "partido": comedor.partido if comedor.partido else "",
                    "barrio": comedor.barrio if comedor.barrio else "",
                    "codigo_postal": (
                        comedor.codigo_postal if comedor.codigo_postal else ""
                    ),
                    "Referente": (
                        comedor.referente.documento
                        if comedor.referente and comedor.referente.documento
                        else ""
                    ),
                    "Imagen": (
                        f"{os.getenv('DOMINIO')}/media/{comedor.foto_legajo}"
                        if comedor.foto_legajo
                        else ""
                    ),
                }
            ],
        }

        headers = {
            "applicationAccessKey": os.getenv("GESTIONAR_API_KEY"),
        }

        try:
            response = requests.post(
                os.getenv("GESTIONAR_API_CREAR_COMEDOR"),
                json=data,
                headers=headers,
                timeout=TIMEOUT,
            )
            response.raise_for_status()
            response = response.json()
            print(f"COMEDOR {comedor.id} sincronizado con GESTIONAR con exito")
        except Exception as e:
            print("!!! Error al sincronizar creacion de COMEDOR con GESTIONAR:")
            print(e)
            print("!!! Con el body:")
            print(data)


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
