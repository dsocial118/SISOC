from typing import Union

from django.db.models import Q

from comedores.models import Comedor, Referente
from legajos.models import LegajoProvincias, LegajoMunicipio, LegajoLocalidad


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
                | Q(referente__celular=query)
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
        provincia_obj = LegajoProvincias.objects.filter(
            nombre__iexact=data["provincia"]
        ).first()
        data["provincia"] = provincia_obj.id if provincia_obj else None

        municipio_obj = LegajoMunicipio.objects.filter(
            nombre__iexact=data["municipio"]
        ).first()
        data["municipio"] = municipio_obj.id if municipio_obj else None

        localidad_obj = LegajoLocalidad.objects.filter(
            nombre__iexact=data["localidad"]
        ).first()
        data["localidad"] = localidad_obj.id if localidad_obj else None

    @staticmethod
    def create_referente(data):
        referente = Referente.objects.create(
            nombre=data["referente"]["nombre"],
            apellido=data["referente"]["apellido"],
            celular=data["referente"]["celular"].replace("-", ""),
            mail=data["referente"]["mail"],
            documento=data["referente"]["documento"].replace(".", ""),
        )

        return referente
