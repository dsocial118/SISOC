import logging
from typing import Union
from django.db.models import Q
from django.shortcuts import get_object_or_404
from cdi.models import CentroDesarrolloInfantil
from core.models import Mes, Dia, Turno

logger = logging.getLogger("django")


class CentroDesarrolloInfantilService:
    @staticmethod
    def get_centros_filtrados(query: Union[str, None] = None):
        """
        Filtra los centros de desarrollo infantil según la consulta.
        """
        try:
            queryset = CentroDesarrolloInfantil.objects.values(
                "id", "nombre", "provincia", "municipio", "localidad", "direccion"
            )

            if query:
                queryset = queryset.filter(
                    Q(nombre__icontains=query)
                    | Q(provincia__icontains=query)
                    | Q(municipio__icontains=query)
                    | Q(localidad__icontains=query)
                )
            return queryset
        except Exception:
            logger.exception(
                "Error en CentroDesarrolloInfantilService.get_centros_filtrados",
                extra={"query": query},
            )
            raise

    @staticmethod
    def get_centro_detail_object(centro_id: int):
        """
        Obtiene un centro específico con todos sus detalles.
        """
        try:
            return get_object_or_404(
                CentroDesarrolloInfantil.objects.select_related(
                    "provincia",
                    "municipio",
                    "localidad",
                ),
                pk=centro_id,
            )
        except Exception:
            logger.exception(
                "Error en CentroDesarrolloInfantilService.get_centro_detail_object",
                extra={"centro_pk": centro_id},
            )
            raise

    @staticmethod
    def create_imagenes(imagen, centro_id):
        """
        Permite asociar imágenes al CDI.
        """
        try:
            from .forms import ImagenCentroDesarrolloInfantilForm

            imagen_centro = ImagenCentroDesarrolloInfantilForm(
                {"centro": centro_id}, {"imagen": imagen}
            )
            if imagen_centro.is_valid():
                return imagen_centro.save()
            else:
                return imagen_centro.errors
        except Exception:
            logger.exception(
                "Error en CentroDesarrolloInfantilService.create_imagenes",
                extra={"centro_pk": centro_id},
            )
            raise

    @staticmethod
    def get_mes_dia_turno_ids(data):
        """
        Asocia IDs de meses, días y turnos a un centro.
        """
        try:
            if "meses_funcionamiento" in data:
                meses = Mes.objects.filter(nombre__in=data["meses_funcionamiento"])
                data["meses_funcionamiento"] = meses

            if "dias_funcionamiento" in data:
                dias = Dia.objects.filter(nombre__in=data["dias_funcionamiento"])
                data["dias_funcionamiento"] = dias

            if "turnos_funcionamiento" in data:
                turnos = Turno.objects.filter(nombre__in=data["turnos_funcionamiento"])
                data["turnos_funcionamiento"] = turnos

            return data
        except Exception:
            logger.exception(
                "Error en CentroDesarrolloInfantilService.get_mes_dia_turno_ids",
                extra={"data": data},
            )
            raise

    @staticmethod
    def get_informacion_adicional(centro_id: int):
        """
        Devuelve datos adicionales de un centro, como estadísticas o detalles personalizados.
        """
        try:
            centro = CentroDesarrolloInfantil.objects.get(pk=centro_id)
            return {
                "total_ninos": centro.cantidad_ninos,
                "total_trabajadores": centro.cantidad_trabajadores,
                "horario": f"{centro.horario_inicio} - {centro.horario_fin}",
            }
        except Exception:
            logger.exception(
                "Error en CentroDesarrolloInfantilService.get_informacion_adicional",
                extra={"centro_pk": centro_id},
            )
            raise
