from django.db.models import Q, QuerySet
from django.core.cache import cache

from config.settings import CACHE_TIMEOUT
from legajos.models import (
    LegajoLocalidad,
    LegajoMunicipio,
    LegajoProvincias,
    Legajos,
    LegajosDerivaciones,
)


class LegajosService:
    @staticmethod
    def obtener_queryset_filtrado(query: str) -> QuerySet[Legajos]:
        queryset = Legajos.objects.only(
            "id",
            "apellido",
            "nombre",
            "documento",
            "tipo_doc",
            "sexo",
            "localidad",
            "estado",
        )

        if query:
            filter_condition = Q(apellido__icontains=query)
            if query.isnumeric():
                filter_condition |= Q(documento__contains=query)
            queryset = queryset.filter(filter_condition)

        return queryset

    @staticmethod
    def obtener_municipios(provincia_id: int) -> list[LegajoMunicipio]:
        provincias = cache.get_or_set(
            "provincias", LegajoProvincias.objects.all(), CACHE_TIMEOUT
        )
        municipios = cache.get_or_set(
            "municipios", LegajoMunicipio.objects.all(), CACHE_TIMEOUT
        )

        provincia = provincias.objects.get(id=provincia_id)
        municipios = municipios.objects.filter(
            codigo_ifam__startswith=provincia.abreviatura
        ).values("id", "departamento_id", "nombre_region")

        return list(municipios)

    @staticmethod
    def obtener_localidades(municipio_id: int) -> list[LegajoLocalidad]:
        municipios = cache.get_or_set(
            "municipios", LegajoMunicipio.objects.all(), CACHE_TIMEOUT
        )
        localidades = cache.get_or_set(
            "localidades", LegajoLocalidad.objects.all(), CACHE_TIMEOUT
        )

        municipio = municipios.objects.get(id=municipio_id)
        localidades = localidades.objects.filter(
            departamento_id=municipio.departamento_id
        ).values("id", "nombre")

        return list(localidades)

    @staticmethod
    def obtener_derivaciones(
        programa,
        organismo,
        legajo_nombre,
        estado,
        fecha_desde,
    ) -> QuerySet[LegajosDerivaciones]:
        filters = Q()

        if programa:
            filters &= Q(fk_programa=programa)
        if organismo:
            filters &= Q(fk_organismo=organismo)
        if legajo_nombre:
            filters &= (
                Q(fk_legajo__nombre__icontains=legajo_nombre)
                | Q(fk_legajo__apellido__icontains=legajo_nombre)
                | Q(fk_legajo__documento__icontains=legajo_nombre)
            )
        if estado:
            filters &= Q(estado=estado)
        if fecha_desde:
            filters &= Q(fecha_creado__gte=fecha_desde)

        return (
            LegajosDerivaciones.objects.filter(filters)
            .select_related("fk_programa", "fk_organismo", "fk_legajo")
            .distinct()
            .values(
                "fk_legajo__id",
                "fk_legajo__nombre",
                "fk_legajo__tipo_doc",
                "fk_legajo__documento",
                "fk_legajo__sexo",
                "fk_programa",
                "fk_organismo",
                "estado",
            )
        )
