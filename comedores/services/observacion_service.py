import os

import requests

from comedores.models import Observacion


class ObservacionService:
    @staticmethod
    def send_to_gestionar(observacion: Observacion):
        if observacion.gestionar_uid is None:
            data = {
                "Action": "Add",
                "Properties": {"Locale": "es-ES"},
                "Rows": [
                    {
                        "Comedor_Id": observacion.comedor.gestionar_uid,
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

            try:
                response = requests.post(
                    os.getenv("GESTIONAR_API_CREAR_OBSERVACION"),
                    json=data,
                    headers=headers,
                )
                response.raise_for_status()
                response = response.json()

                observacion.gestionar_uid = response["Rows"][0]["ID_Observacion"]
                observacion.save()
            except requests.exceptions.RequestException as e:
                print(f"Error en la petición POST: {e}")
