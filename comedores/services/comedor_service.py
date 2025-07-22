import re
from typing import Union

from django.db.models import Q, Count, Prefetch
from django.core.paginator import Paginator
from django.core.cache import cache
from django.conf import settings

from relevamientos.models import Relevamiento, ClasificacionComedor
from comedores.forms.comedor_form import ImagenComedorForm
from comedores.models import Comedor, Referente, ValorComida, Nomina, Observacion
from admisiones.models.admisiones import Admision
from rendicioncuentasmensual.models import RendicionCuentaMensual
from intervenciones.models.intervenciones import Intervencion
from core.models import Municipio, Prestacion, Provincia
from core.models import Localidad
from comedores.models import ImagenComedor


class ComedorService:
    @staticmethod
    def get_comedor_by_dupla(id_dupla):
        return Comedor.objects.filter(dupla=id_dupla).first()

    @staticmethod
    def get_comedor(pk_send, as_dict=False):
        if as_dict:
            return Comedor.objects.values(
                "id", "nombre", "provincia", "barrio", "calle", "numero"
            ).get(pk=pk_send)
        return Comedor.objects.get(pk=pk_send)

    @staticmethod
    def detalle_de_intervencion(kwargs):
        intervenciones = Intervencion.objects.filter(comedor=kwargs["pk"])
        cantidad_intervenciones = Intervencion.objects.filter(
            comedor=kwargs["pk"]
        ).count()

        return intervenciones, cantidad_intervenciones

    @staticmethod
    def asignar_dupla_a_comedor(dupla_id, comedor_id):
        comedor = Comedor.objects.get(id=comedor_id)
        comedor.dupla_id = dupla_id
        comedor.estado = "Asignado a Dupla Técnica"
        comedor.save()
        return comedor

    @staticmethod
    def borrar_imagenes(post):
        pattern = re.compile(r"^imagen_ciudadano-borrar-(\d+)$")
        imagenes_ids = []
        for key in post:
            match = pattern.match(key)
            if match:
                imagen_id = match.group(1)
                imagenes_ids.append(imagen_id)

        ImagenComedor.objects.filter(id__in=imagenes_ids).delete()

    @staticmethod
    def get_comedores_filtrados(query: Union[str, None] = None):
        # Optimización: usar select_related en lugar de prefetch_related con values()
        queryset = (
            Comedor.objects.select_related(
                "provincia", "municipio", "localidad", "referente", "tipocomedor"
            )
            .values(
                "id",
                "nombre",
                "tipocomedor__nombre",
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
            .order_by("-id")
        )
        if query:
            queryset = queryset.filter(
                Q(nombre__icontains=query)
                | Q(tipocomedor__nombre__icontains=query)
                | Q(provincia__nombre__icontains=query)
                | Q(municipio__nombre__icontains=query)
                | Q(localidad__nombre__icontains=query)
                | Q(barrio__icontains=query)
                | Q(calle__icontains=query)
            )
        return queryset

    @staticmethod
    def get_comedor_detail_object(comedor_id: int):
        # Precargar cache de valores de comida para evitar query adicional
        ComedorService._preload_valores_comida_cache()

        return (
            Comedor.objects.select_related(
                "provincia",
                "municipio",
                "localidad",
                "referente",
                "organizacion",
                "programa",
                "tipocomedor",
                "dupla",
            )
            .prefetch_related(
                "expedientes_pagos",
                # Prefetch para imágenes optimizado - solo el campo imagen
                Prefetch(
                    "imagenes",
                    queryset=ImagenComedor.objects.only("imagen"),
                    to_attr="imagenes_optimized",
                ),
                # Prefetch para relevamientos ordenados por estado e id descendente
                Prefetch(
                    "relevamiento_set",
                    queryset=(
                        Relevamiento.objects.order_by(
                            "-estado", "-id"
                        ).prefetch_related(
                            Prefetch(
                                "prestaciones",
                                queryset=Prestacion.objects.only("id"),
                                to_attr="prestaciones_opt",
                            )
                        )
                    ),
                    to_attr="relevamientos_optimized",
                ),
                # Prefetch para observaciones ordenadas por fecha de visita (solo las últimas 3)
                Prefetch(
                    "observacion_set",
                    queryset=Observacion.objects.order_by("-fecha_visita")[:3],
                    to_attr="observaciones_optimized",
                ),
                # Prefetch para clasificaciones ordenadas por fecha (solo la primera)
                Prefetch(
                    "clasificacioncomedor_set",
                    queryset=ClasificacionComedor.objects.select_related(
                        "categoria"
                    ).order_by("-fecha"),
                    to_attr="clasificaciones_optimized",
                ),
                # Prefetch para admisiones
                Prefetch(
                    "admision_set",
                    queryset=Admision.objects.select_related("tipo_convenio", "estado"),
                    to_attr="admisiones_optimized",
                ),
                # Prefetch para rendiciones mensuales - solo contar
                Prefetch(
                    "rendiciones_cuentas_mensuales",
                    queryset=RendicionCuentaMensual.objects.only("id"),
                    to_attr="rendiciones_optimized",
                ),
            )
            .get(pk=comedor_id)
        )

    @staticmethod
    def _preload_valores_comida_cache():
        """Precarga los valores de comida en cache para evitar queries adicionales"""
        from django.core.cache import cache

        valor_map = cache.get("valores_comida_map")
        if not valor_map:
            valores_comida = ValorComida.objects.filter(
                tipo__in=[
                    "desayuno",
                    "almuerzo",
                    "merienda",
                    "cena",
                ]
            ).values("tipo", "valor")
            valor_map = {item["tipo"].lower(): item["valor"] for item in valores_comida}
            cache.set(
                "valores_comida_map", valor_map, settings.DEFAULT_CACHE_TIMEOUT
            )  # Cache por 5 minutos

    @staticmethod
    def get_ubicaciones_ids(data):
        if "provincia" in data:
            provincia_obj = Provincia.objects.filter(
                nombre__iexact=data["provincia"]
            ).first()
            data["provincia"] = provincia_obj.id if provincia_obj else ""

        if "municipio" in data:
            municipio_obj = Municipio.objects.filter(
                nombre__iexact=data["municipio"]
            ).first()
            data["municipio"] = municipio_obj.id if municipio_obj else ""

        if "localidad" in data:
            localidad_obj = Localidad.objects.filter(
                nombre__iexact=data["localidad"]
            ).first()
            data["localidad"] = localidad_obj.id if localidad_obj else ""

        return data

    @staticmethod
    def create_or_update_referente(data, referente_instance=None):
        referente_data = data.get("referente", {})

        if "celular" in referente_data:
            referente_data["celular"] = referente_data["celular"].replace("-", "")
            if referente_data["celular"] == "":
                referente_data["celular"] = None
        if "documento" in referente_data:
            referente_data["documento"] = referente_data["documento"].replace(".", "")

        if referente_instance is None:
            referente_instance = Referente.objects.create(**referente_data)
        else:
            for field, value in referente_data.items():
                setattr(referente_instance, field, value)
            referente_instance.save(update_fields=referente_data.keys())

        return referente_instance

    @staticmethod
    def create_imagenes(imagen, comedor_pk):
        imagen_comedor = ImagenComedorForm(
            {"comedor": comedor_pk},
            {"imagen": imagen},
        )
        if imagen_comedor.is_valid():
            return imagen_comedor.save()
        else:
            return imagen_comedor.errors

    @staticmethod
    def get_presupuestos(comedor_id: int, relevamientos_prefetched=None):
        from django.core.cache import cache

        # Cache de valores de comida para evitar consultas repetidas
        valor_map = cache.get("valores_comida_map")
        if not valor_map:
            valores_comida = ValorComida.objects.filter(
                tipo__in=["desayuno", "almuerzo", "merienda", "cena"]
            ).values("tipo", "valor")
            valor_map = {item["tipo"].lower(): item["valor"] for item in valores_comida}
            cache.set(
                "valores_comida_map", valor_map, settings.DEFAULT_CACHE_TIMEOUT
            )  # Cache por 5 minutos

        # Usar relevamientos prefetched si están disponibles
        if relevamientos_prefetched:
            beneficiarios = (
                relevamientos_prefetched[0] if relevamientos_prefetched else None
            )
        else:
            # Fallback: consulta directa solo si no hay datos prefetched
            beneficiarios = (
                Relevamiento.objects.prefetch_related("prestaciones")
                .filter(comedor=comedor_id)
                .only("prestaciones")
                .first()
            )

        count = {
            "desayuno": 0,
            "almuerzo": 0,
            "merienda": 0,
            "cena": 0,
            "merienda_reforzada": 0,
        }

        if beneficiarios and beneficiarios.prestaciones:
            for prestacion in beneficiarios.prestaciones.all():
                dias = [
                    "lunes",
                    "martes",
                    "miercoles",
                    "jueves",
                    "viernes",
                    "sabado",
                    "domingo",
                ]
                tipos = ["desayuno", "almuerzo", "merienda", "cena"]

                for tipo in tipos:
                    count[tipo] = sum(
                        getattr(prestacion, f"{dia}_{tipo}_actual", 0) or 0
                        for dia in dias
                    )

        count_beneficiarios = sum(count.values())

        # Usar valores de comida cacheados
        valor_cena = count["cena"] * valor_map.get("cena", 0)
        valor_desayuno = count["desayuno"] * valor_map.get("desayuno", 0)
        valor_almuerzo = count["almuerzo"] * valor_map.get("almuerzo", 0)
        valor_merienda = count["merienda"] * valor_map.get("merienda", 0)

        return (
            count_beneficiarios,
            valor_cena,
            valor_desayuno,
            valor_almuerzo,
            valor_merienda,
        )

    @staticmethod
    def detalle_de_nomina(comedor_pk, page=1, per_page=100):
        qs_nomina = Nomina.objects.filter(comedor_id=comedor_pk).select_related(
            "ciudadano__sexo", "estado"
        )

        resumen = qs_nomina.aggregate(
            cantidad_nomina_m=Count("id", filter=Q(ciudadano__sexo__sexo="Masculino")),
            cantidad_nomina_f=Count("id", filter=Q(ciudadano__sexo__sexo="Femenino")),
            espera=Count("id", filter=Q(estado__nombre="Lista de espera")),
            cantidad_total=Count("id"),
        )

        paginator = Paginator(
            qs_nomina.only(
                "fecha",
                "ciudadano__apellido",
                "ciudadano__nombre",
                "ciudadano__sexo",
                "ciudadano__documento",
                "estado",
            ),
            per_page,
        )
        page_obj = paginator.get_page(page)

        return (
            page_obj,
            resumen["cantidad_nomina_m"],
            resumen["cantidad_nomina_f"],
            resumen["espera"],
            resumen["cantidad_total"],
        )
