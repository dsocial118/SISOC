import calendar
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Union

from django.core.cache import cache
from django.db.models import (
    Case,
    Count,
    ForeignKey,
    IntegerField,
    ManyToManyField,
    Q,
    QuerySet,
    Value,
    When,
)

from config.settings import CACHE_TIMEOUT
from configuraciones.choices import CHOICE_DIMENSIONES
from legajos.models import (
    DimensionFamilia,
    DimensionSalud,
    DimensionTrabajo,
    DimensionVivienda,
    HistorialLegajoAlertas,
    LegajoAlertas,
    LegajoGrupoFamiliar,
    LegajoGrupoHogar,
    LegajoLocalidad,
    LegajoMunicipio,
    LegajoProvincias,
    Legajos,
    LegajosArchivos,
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
            "estado",
        )

        if query:
            filter_condition = Q(apellido__icontains=query)
            if query.isnumeric():
                filter_condition |= Q(documento__contains=query)
            queryset = queryset.filter(filter_condition)

        return queryset

    @staticmethod
    def obtener_municipios(
        provincia_id: Union[int, None]
    ) -> List[Dict[str, Union[str, int]]]:
        provincias = cache.get_or_set(
            "provincias", LegajoProvincias.objects.all(), CACHE_TIMEOUT
        )
        municipios = cache.get_or_set(
            "municipios", LegajoMunicipio.objects.all(), CACHE_TIMEOUT
        )

        if provincia_id is None:
            municipios = municipios.values("id", "departamento_id", "nombre_region")
        else:
            provincia = provincias.get(id=provincia_id)
            municipios = municipios.filter(
                codigo_ifam__startswith=provincia.abreviatura
            ).values("id", "departamento_id", "nombre_region")

        return list(municipios)

    @staticmethod
    def obtener_localidades(
        municipio_id: Union[int, None]
    ) -> List[Dict[str, Union[str, int]]]:
        municipios = cache.get_or_set(
            "municipios", LegajoMunicipio.objects.all(), CACHE_TIMEOUT
        )
        localidades = cache.get_or_set(
            "localidades", LegajoLocalidad.objects.all(), CACHE_TIMEOUT
        )

        if municipio_id is None:
            localidades = localidades.values("id", "nombre")
        else:
            municipio = municipios.get(id=municipio_id)
            localidades = localidades.filter(
                departamento_id=municipio.departamento_id
            ).values("id", "nombre")

        return list(localidades)

    @staticmethod
    def obtener_derivaciones(
        programa: str,
        organismo: str,
        legajo_nombre: str,
        estado: str,
        fecha_desde: str,
    ) -> QuerySet[Dict[str, Union[int, str]]]:
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
                "fk_programa__nombre",
                "fk_organismo__nombre",
                "estado",
            )
        )

    @staticmethod
    def obtener_extras_legajo(legajo_id: int) -> Dict[str, Any]:
        alertas_categorizadas = LegajosService.obtener_alertas_categorizadas(legajo_id)

        legajos_relacionados = LegajosService.obtener_legajos_relacionados(legajo_id)

        dimensiones = LegajosService.obtener_dimensiones(legajo_id)

        files = cache.get_or_set(
            f"{legajo_id}_files",
            LegajosArchivos.objects.filter(
                Q(tipo="Imagen") | Q(tipo="Documento"), fk_legajo=legajo_id
            ),
            CACHE_TIMEOUT,
        )
        count_intervenciones = cache.get_or_set(
            f"{legajo_id}_count_intervenciones",
            LegajosDerivaciones.objects.filter(fk_legajo=legajo_id).count(),
            CACHE_TIMEOUT,
        )
        alertas = cache.get_or_set(
            f"{legajo_id}_alertas",
            HistorialLegajoAlertas.objects.filter(fk_legajo=legajo_id).values(
                "fecha_inicio", "fecha_fin", "fk_alerta__fk_categoria__dimension"
            ),
            CACHE_TIMEOUT,
        )
        historial_alertas = cache.get_or_set(
            f"{legajo_id}_historial_alertas", alertas.exists(), CACHE_TIMEOUT
        )
        datos_json = cache.get_or_set(
            f"{legajo_id}_datos_json",
            LegajosService.obtener_grafico_evolucion_riesgo(alertas),
            CACHE_TIMEOUT,
        )

        context = {
            "count_familia": legajos_relacionados["count_grupo_familiar"],
            "familiares_fk1": legajos_relacionados["grupo_familiar_fk1"],
            "familiares_fk2": legajos_relacionados["grupo_familiar_fk2"],
            "hogar_count_familia": legajos_relacionados["count_grupo_hogar"],
            "hogar_familiares_fk1": legajos_relacionados["grupo_hogar_fk1"],
            "hogar_familiares_fk2": legajos_relacionados["grupo_hogar_fk2"],
            "files_img": files.filter(tipo="Imagen"),
            "files_docs": files.filter(tipo="Documento"),
            "count_alertas": alertas_categorizadas["count_alertas"],
            "count_alta": alertas_categorizadas["count_alta"],
            "count_media": alertas_categorizadas["count_media"],
            "count_baja": alertas_categorizadas["count_baja"],
            "alertas_alta": alertas_categorizadas["alertas_alta"],
            "alertas_media": alertas_categorizadas["alertas_media"],
            "alertas_baja": alertas_categorizadas["alertas_baja"],
            "historial_alertas": historial_alertas,
            "count_intervenciones": count_intervenciones,
            "dimensionfamilia": dimensiones["dimension_familia"],
            "dimensionvivienda": dimensiones["dimension_vivienda"],
            "dimensionsalud": dimensiones["dimension_salud"],
            "dimensiontrabajo": dimensiones["dimension_trabajo"],
            "datos_json": datos_json,
        }

        return context

    @staticmethod
    def obtener_dimensiones(legajo_id):
        dimension_familia = cache.get_or_set(
            f"{legajo_id}_dimensionfamilia",
            DimensionFamilia.objects.filter(fk_legajo=legajo_id)
            .values(
                "estado_civil",
                "cant_hijos",
                "otro_responsable",
                "hay_embarazadas",
                "hay_priv_libertad",
                "hay_prbl_smental",
                "hay_enf_cronica",
                "obs_familia",
            )
            .first(),
            CACHE_TIMEOUT,
        )
        dimension_vivienda = cache.get_or_set(
            f"{legajo_id}_dimensionvivienda",
            DimensionVivienda.objects.filter(fk_legajo=legajo_id)
            .values(
                "posesion",
                "tipo",
                "material",
                "pisos",
                "cant_ambientes",
                "cant_camas",
                "cant_hogares",
                "cant_convivientes",
                "cant_menores",
                "hay_banio",
                "hay_agua_caliente",
                "hay_desmoronamiento",
                "ContextoCasa",
                "PoseenPC",
                "Poseeninternet",
                "PoseenCeludar",
                "obs_vivienda",
            )
            .first(),
            CACHE_TIMEOUT,
        )
        dimension_salud = cache.get_or_set(
            f"{legajo_id}_dimensionsalud",
            DimensionSalud.objects.filter(fk_legajo=legajo_id)
            .values(
                "lugares_atencion",
                "frec_controles",
                "hay_enfermedad",
                "hay_obra_social",
                "hay_discapacidad",
                "hay_cud",
                "obs_salud",
            )
            .first(),
            CACHE_TIMEOUT,
        )
        dimension_trabajo = cache.get_or_set(
            f"{legajo_id}_dimensiontrabajo",
            DimensionTrabajo.objects.filter(fk_legajo=legajo_id)
            .values(
                "tiene_trabajo",
                "ocupacion",
                "modo_contratacion",
                "conviviente_trabaja",
                "obs_trabajo",
            )
            .first(),
            CACHE_TIMEOUT,
        )

        return {
            "dimension_familia": dimension_familia,
            "dimension_vivienda": dimension_vivienda,
            "dimension_salud": dimension_salud,
            "dimension_trabajo": dimension_trabajo,
        }

    @staticmethod
    def obtener_legajos_relacionados(legajo_id) -> Dict[str, List[Dict[str, Any]]]:
        grupo_familiar = cache.get_or_set(
            f"{legajo_id}_familiares",
            LegajoGrupoFamiliar.objects.filter(
                Q(fk_legajo_1=legajo_id) | Q(fk_legajo_2=legajo_id)
            ).values(
                "fk_legajo_1__nombre",
                "fk_legajo_1__apellido",
                "fk_legajo_1__id",
                "fk_legajo_1__foto",
                "fk_legajo_2__nombre",
                "fk_legajo_2__apellido",
                "fk_legajo_2__id",
                "fk_legajo_2__foto",
                "vinculo",
                "vinculo_inverso",
            ),
            CACHE_TIMEOUT,
        )

        grupo_hogar = cache.get_or_set(
            f"{legajo_id}_hogar_familiares",
            LegajoGrupoHogar.objects.filter(
                Q(fk_legajo_1Hogar=legajo_id) | Q(fk_legajo_2Hogar=legajo_id)
            ).values(
                "fk_legajo_2Hogar_id",
                "fk_legajo_2Hogar",
                "fk_legajo_1Hogar_id",
                "fk_legajo_1Hogar",
                "fk_legajo_1Hogar__nombre",
                "fk_legajo_2Hogar__nombre",
                "fk_legajo_1Hogar__foto",
                "fk_legajo_2Hogar__foto",
                "estado_relacion",
            ),
            CACHE_TIMEOUT,
        )

        return {
            "count_grupo_familiar": len(grupo_familiar),
            "grupo_familiar_fk1": [
                legajo
                for legajo in grupo_familiar
                if legajo["fk_legajo_1__id"] == int(legajo_id)
            ],
            "grupo_familiar_fk2": [
                legajo
                for legajo in grupo_familiar
                if legajo["fk_legajo_2__id"] == int(legajo_id)
            ],
            "count_grupo_hogar": len(grupo_hogar),
            "grupo_hogar_fk1": [
                legajo
                for legajo in grupo_hogar
                if legajo["fk_legajo_1Hogar"] == int(legajo_id)
            ],
            "grupo_hogar_fk2": [
                legajo
                for legajo in grupo_hogar
                if legajo["fk_legajo_2Hogar"] == int(legajo_id)
            ],
        }

    @staticmethod
    def obtener_alertas_categorizadas(
        legajo_id: int,
    ) -> Dict[str, Union[int, QuerySet]]:
        legajo_alertas = cache.get_or_set(
            f"{legajo_id}_legajo_alertas",
            LegajoAlertas.objects.filter(fk_legajo=legajo_id).select_related(
                "fk_alerta__fk_categoria"
            ),
            CACHE_TIMEOUT,
        )
        legajo_alertas_organizadas = cache.get_or_set(
            f"{legajo_id}_legajo_alertas_organizadas",
            legajo_alertas.annotate(
                es_critica=Case(
                    When(fk_alerta__gravedad="Critica", then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField(),
                ),
                es_importante=Case(
                    When(fk_alerta__gravedad="Importante", then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField(),
                ),
                es_precaucion=Case(
                    When(fk_alerta__gravedad="Precaución", then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField(),
                ),
            ),
            CACHE_TIMEOUT,
        )
        count_alertas = cache.get_or_set(
            f"{legajo_id}_count_alertas", legajo_alertas.count(), CACHE_TIMEOUT
        )
        count_alta = cache.get_or_set(
            f"{legajo_id}_count_alta",
            legajo_alertas_organizadas.aggregate(count=Count("es_critica")).get(
                "count", 0
            ),
            CACHE_TIMEOUT,
        )
        count_media = cache.get_or_set(
            f"{legajo_id}_count_media",
            legajo_alertas_organizadas.aggregate(count=Count("es_importante")).get(
                "count", 0
            ),
            CACHE_TIMEOUT,
        )
        count_baja = cache.get_or_set(
            f"{legajo_id}_count_baja",
            legajo_alertas_organizadas.aggregate(count=Count("es_precaucion")).get(
                "count", 0
            ),
            CACHE_TIMEOUT,
        )
        alertas_alta = cache.get_or_set(
            f"{legajo_id}_alertas_alta",
            legajo_alertas_organizadas.filter(es_critica=True),
            CACHE_TIMEOUT,
        )
        alertas_media = cache.get_or_set(
            f"{legajo_id}_alertas_media",
            legajo_alertas_organizadas.filter(es_importante=True),
            CACHE_TIMEOUT,
        )
        alertas_baja = cache.get_or_set(
            f"{legajo_id}_alertas_baja",
            legajo_alertas_organizadas.filter(es_precaucion=True),
            CACHE_TIMEOUT,
        )

        return {
            "count_alertas": count_alertas,
            "count_alta": count_alta,
            "count_media": count_media,
            "count_baja": count_baja,
            "alertas_alta": alertas_alta,
            "alertas_media": alertas_media,
            "alertas_baja": alertas_baja,
        }

    @staticmethod
    def obtener_grafico_evolucion_riesgo(alertas: QuerySet) -> Union[str, Dict]:
        fecha_actual = datetime.now().date()

        if alertas.exists():
            doce_meses_previos = datetime(
                fecha_actual.year, fecha_actual.month % 12 + 1, 1
            ) - timedelta(days=365)

            alertas_ultimo_anio = alertas.filter(
                Q(fecha_inicio__gt=doce_meses_previos)
                | Q(fecha_fin__gt=doce_meses_previos)
                | Q(fecha_fin__isnull=True)
            ).distinct()

            dimensiones = {
                key.strip(): value
                for key, value in CHOICE_DIMENSIONES
                if key is not None
            }
            dimensiones = list(dimensiones.keys())
            datos_por_dimension = {dimension: [0] * 12 for dimension in dimensiones}

            for alerta in alertas_ultimo_anio:
                dimension = alerta["fk_alerta__fk_categoria__dimension"]
                fecha_inicio = alerta["fecha_inicio"]
                fecha_fin = alerta["fecha_fin"] or fecha_actual

                meses_activos = []
                while fecha_inicio <= fecha_fin:
                    meses_activos.append(fecha_inicio.month)
                    fecha_inicio = fecha_inicio.replace(day=1) + timedelta(days=32)
                    fecha_inicio = fecha_inicio.replace(day=1)

                for mes in meses_activos:
                    datos_por_dimension[dimension][mes - 1] += 1

            mes_actual = fecha_actual.month
            datos_por_dimension = {
                dimension: datos_por_dimension[dimension][mes_actual:]
                + datos_por_dimension[dimension][:mes_actual]
                for dimension in dimensiones
            }

            nombres_meses = [
                calendar.month_name[mes].capitalize() for mes in range(1, 13)
            ]
            nombres_meses_ordenados = (
                nombres_meses[mes_actual:] + nombres_meses[:mes_actual]
            )

            datos_por_dimension["meses"] = nombres_meses_ordenados

            return json.dumps(datos_por_dimension)

        return {}

    @staticmethod
    def obtener_relaciones(legajo: int) -> List[str]:
        relaciones_existentes = []

        for field in legajo._meta.get_fields():
            if isinstance(field, (ForeignKey, ManyToManyField)):
                related_model_class = field.related_model
                related_model_name = related_model_class.__name__
                related_model = getattr(legajo, field.name, None)
                if related_model:
                    relaciones_existentes.append(
                        related_model_name,  # Guardar el nombre del modelo relacionado
                    )

        return relaciones_existentes
