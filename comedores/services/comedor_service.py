import os
from typing import Union

from django.db.models import Q
import requests

from comedores.models import Comedor, Referente
from configuraciones.models import Municipio, Provincias
from configuraciones.models import Localidad


class ComedorService:
    @staticmethod
    def get_comedores_filtrados(query: Union[str, None] = None):
        queryset = Comedor.objects.prefetch_related("provincia", "referente").values(
            "id",
            "nombre",
            "provincia__nombre",
            "municipio__nombre",
            "localidad__nombre",
            "barrio",
            "partido",
            "calle",
            "numero",
            "referente__nombre",
            "referente__apellido",
            "referente__celular",
        )
        if query:
            queryset = queryset.filter(
                Q(nombre__icontains=query)
                | Q(provincia__nombre__icontains=query)
                | Q(municipio__nombre=query)
                | Q(localidad__nombre=query)
                | Q(referente__nombre=query)
                | Q(referente__apellido=query)
            )
        return queryset

    @staticmethod
    def get_comedor_detail_object(comedor_id: int):
        return (
            Comedor.objects.select_related("provincia", "referente")
            .values(
                "id",
                "nombre",
                "comienzo",
                "provincia__nombre",
                "municipio__nombre",
                "localidad__nombre",
                "partido",
                "barrio",
                "calle",
                "numero",
                "entre_calle_1",
                "entre_calle_2",
                "codigo_postal",
                "referente__nombre",
                "referente__apellido",
                "referente__mail",
                "referente__celular",
                "referente__documento",
            )
            .get(pk=comedor_id)
        )

    @staticmethod
    def get_ubicaciones_ids(data):
        if "provincia" in data:
            provincia_obj = Provincias.objects.filter(
                nombre__iexact=data["provincia"]
            ).first()
            data["provincia"] = provincia_obj.id if provincia_obj else None

        if "municipio" in data:
            municipio_obj = Municipio.objects.filter(
                nombre__iexact=data["municipio"]
            ).first()
            data["municipio"] = municipio_obj.id if municipio_obj else None

        if "localidad" in data:
            localidad_obj = Localidad.objects.filter(
                nombre__iexact=data["localidad"]
            ).first()
            data["localidad"] = localidad_obj.id if localidad_obj else None

        return data

    @staticmethod
    def create_or_update_referente(data, referente_instance=None):
        referente_data = data.get("referente", {})

        if "celular" in referente_data:
            referente_data["celular"] = referente_data["celular"].replace("-", "")
        if "documento" in referente_data:
            referente_data["documento"] = referente_data["documento"].replace(".", "")

        if referente_instance is None:  # Crear referente
            referente_instance = Referente.objects.create(**referente_data)
        else:  # Actualizar referente
            for field, value in referente_data.items():
                setattr(referente_instance, field, value)
            referente_instance.save()

        return referente_instance

    @staticmethod
    def send_to_gestionar(comedor: Comedor):

        if comedor.gestionar_uid is None:
            data = {
                "Action": "Add",
                "Properties": {"Locale": "es-ES"},
                "Rows": [
                    {
                        "nombre": comedor.nombre,
                        "comienzo": comedor.comienzo,
                        "calle": comedor.calle,
                        "numero": comedor.numero,
                        "entre_calle_1": comedor.entre_calle_1,
                        "entre_calle_2": comedor.entre_calle_2,
                        "provincia": (
                            comedor.provincia.nombre if comedor.provincia else None
                        ),
                        "municipio": (
                            comedor.municipio.nombre if comedor.municipio else None
                        ),
                        "localidad": (
                            comedor.localidad.nombre if comedor.localidad else None
                        ),
                        "partido": comedor.partido,
                        "barrio": comedor.barrio,
                        "codigo_postal": comedor.codigo_postal,
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
                )
                response.raise_for_status()
                response = response.json()

                comedor.gestionar_uid = response["Rows"][0]["ComedorID"]
                comedor.save()
            except requests.exceptions.RequestException as e:
                print(f"Error en la petición POST: {e}")
