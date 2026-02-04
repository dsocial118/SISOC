import logging
import re
from datetime import date, datetime
from typing import Any
import unicodedata

from django.db.models import (
    Q,
    Count,
    Prefetch,
    QuerySet,
    Value,
    IntegerField,
    F,
    Func,
)
from django.db import transaction
from django.core.paginator import Paginator
from django.core.files.storage import default_storage
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.shortcuts import get_object_or_404
from django.db.models.functions import Coalesce, Now
from django.utils.html import format_html

from relevamientos.models import Relevamiento, ClasificacionComedor
from relevamientos.service import RelevamientoService
from ciudadanos.models import Ciudadano
from comedores.forms.comedor_form import ImagenComedorForm
from comedores.models import (
    Comedor,
    AuditComedorPrograma,
    ImagenComedor,
    Nomina,
    Observacion,
    Referente,
)
from comedores.utils import (
    get_object_by_filter,
    get_id_by_nombre,
    normalize_field,
    preload_valores_comida_cache,
)
from centrodefamilia.services.consulta_renaper import consultar_datos_renaper
from core.models import Provincia, Municipio, Localidad, Nacionalidad
from acompanamientos.models.hitos import Hitos
from admisiones.models.admisiones import Admision
from rendicioncuentasmensual.models import RendicionCuentaMensual
from intervenciones.models.intervenciones import Intervencion
from duplas.models import Dupla

logger = logging.getLogger("django")

from core.constants import UserGroups
from core.security import safe_redirect
from core.services.advanced_filters import AdvancedFilterEngine
from comedores.services.filter_config import (
    CHOICE_OPS,
    FIELD_MAP,
    FIELD_TYPES,
    NUM_OPS,
    TEXT_OPS,
)


COMEDOR_ADVANCED_FILTER = AdvancedFilterEngine(
    field_map=FIELD_MAP,
    field_types=FIELD_TYPES,
    allowed_ops={
        "text": TEXT_OPS,
        "number": NUM_OPS,
        "choice": CHOICE_OPS,
    },
    field_casts={
        "latitud": float,
        "longitud": float,
    },
)


class TimestampDiffYears(Func):
    function = "TIMESTAMPDIFF"
    template = "%(function)s(YEAR, %(expressions)s)"
    output_field = IntegerField()


class ComedorService:
    """Operaciones de alto nivel relacionadas a comedores."""

    @staticmethod
    def get_comedor_by_dupla(id_dupla):
        """Devuelve el primer comedor asociado a la dupla dada."""
        return get_object_by_filter(Comedor, dupla=id_dupla)

    @staticmethod
    def get_comedor(pk_send, as_dict=False):
        if as_dict:
            return Comedor.objects.values(
                "id", "nombre", "provincia", "barrio", "calle", "numero"
            ).get(pk=pk_send)
        return Comedor.objects.get(pk=pk_send)

    @staticmethod
    def get_intervencion_detail(kwargs):
        intervenciones = Intervencion.objects.filter(comedor=kwargs["pk"])
        cantidad_intervenciones = Intervencion.objects.filter(
            comedor=kwargs["pk"]
        ).count()
        return intervenciones, cantidad_intervenciones

    @staticmethod
    def get_admision_timeline_context(admisiones_qs):
        admision_activa = admisiones_qs.filter(activa=True).order_by("-id").first()
        admision_enviada = bool(
            admision_activa
            and getattr(admision_activa, "enviado_acompaniamiento", False)
        )

        if admision_enviada:
            admision_step_class = "step completed"
            admision_circle_html = format_html('<i class="bi bi-check-lg"></i>')
            connector_class = "connector completed"
            ejecucion_step_class = "step active"
        else:
            admision_step_class = "step active"
            admision_circle_html = "1"
            connector_class = "connector"
            ejecucion_step_class = "step"

        return {
            "admision_activa": admision_activa,
            "timeline_admision_step_class": admision_step_class,
            "timeline_admision_circle_html": admision_circle_html,
            "timeline_admision_date": getattr(admision_activa, "creado", None),
            "timeline_connector_class": connector_class,
            "timeline_ejecucion_step_class": ejecucion_step_class,
            "timeline_ejecucion_circle": "2",
            "timeline_rendicion_circle": "3",
        }

    @staticmethod
    def get_admision_timeline_context_from_admision(admision):
        admision_enviada = bool(
            admision and getattr(admision, "enviado_acompaniamiento", False)
        )

        if admision_enviada:
            admision_step_class = "step completed"
            admision_circle_html = format_html('<i class="bi bi-check-lg"></i>')
            connector_class = "connector completed"
            ejecucion_step_class = "step active"
        else:
            admision_step_class = "step active"
            admision_circle_html = "1"
            connector_class = "connector"
            ejecucion_step_class = "step"

        return {
            "timeline_admision_step_class": admision_step_class,
            "timeline_admision_circle_html": admision_circle_html,
            "timeline_admision_date": getattr(admision, "creado", None),
            "timeline_connector_class": connector_class,
            "timeline_ejecucion_step_class": ejecucion_step_class,
            "timeline_ejecucion_circle": "2",
            "timeline_rendicion_circle": "3",
        }

    @staticmethod
    def asignar_dupla_a_comedor(dupla_id, comedor_id):
        comedor = Comedor.objects.get(id=comedor_id)
        comedor.dupla_id = dupla_id
        comedor.estado = "Asignado a Dupla Técnica"
        comedor.save()
        return comedor

    @staticmethod
    def delete_images(post):
        pattern = re.compile(r"^imagen_ciudadano-borrar-(\d+)$")
        imagenes_ids = []
        for key in post:
            match = pattern.match(key)
            if match:
                imagen_id = match.group(1)
                imagenes_ids.append(imagen_id)

        ImagenComedor.objects.filter(id__in=imagenes_ids).delete()

    @staticmethod
    def delete_legajo_photo(post, comedor_instance):
        """Eliminar la foto del legajo si está marcada para borrar"""
        if "foto_legajo_borrar" in post and comedor_instance.foto_legajo:
            archivo = comedor_instance.foto_legajo.name
            if archivo:
                try:
                    default_storage.delete(archivo)
                except Exception:
                    logger.exception(
                        "Error al eliminar la foto de legajo del comedor %s",
                        comedor_instance.pk,
                    )
            comedor_instance.foto_legajo = None
            comedor_instance.save(update_fields=["foto_legajo"])

    @staticmethod
    def get_filtered_comedores(request_or_get: Any, user=None) -> QuerySet:
        """
        Filtra comedores usando el JSON avanzado recibido en el parámetro GET
        ``filters``. La construcción del ``Q`` final se delega en
        ``COMEDOR_ADVANCED_FILTER`` para poder reutilizar el mismo parser en
        otras vistas de listado.

        Si se proporciona un usuario, filtra los comedores según sus permisos:
        - Superusuario: ve todos los comedores
        - Coordinador de Gestión: ve comedores de sus duplas asignadas
        - Técnico/Abogado de dupla: ve comedores donde está asignado
        """

        base_qs = (
            Comedor.objects.select_related(
                "provincia",
                "municipio",
                "localidad",
                "referente",
                "tipocomedor",
                "ultimo_estado__estado_general__estado_actividad",
                "ultimo_estado__estado_general__estado_proceso",
                "ultimo_estado__estado_general__estado_detalle",
            )
            .annotate(
                estado_general=Coalesce(
                    "ultimo_estado__estado_general__estado_actividad__estado",
                    Value(Comedor.ESTADO_GENERAL_DEFAULT),
                )
            )
            .values(
                "id",
                "nombre",
                "estado_general",
                "tipocomedor__nombre",
                "organizacion__nombre",
                "programa__nombre",
                "dupla__nombre",
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
                "ultimo_estado__estado_general__estado_actividad__estado",
                "ultimo_estado__estado_general__estado_proceso",
                "ultimo_estado__estado_general__estado_detalle",
                "estado_validacion",
                "fecha_validado",
            )
            .order_by("-id")
        )

        # Filtrar por usuario si se proporciona
        if user and not user.is_superuser:
            from users.services import UserPermissionService

            if UserPermissionService.tiene_grupo(user, UserGroups.COORDINADOR_GENERAL):
                return COMEDOR_ADVANCED_FILTER.filter_queryset(base_qs, request_or_get)

            # Verificar si es coordinador usando servicio centralizado
            is_coordinador, duplas_ids = UserPermissionService.get_coordinador_duplas(
                user
            )
            is_dupla = UserPermissionService.es_tecnico_o_abogado(user)

            # Aplicar filtros según el rol
            if is_coordinador:
                if not duplas_ids:
                    base_qs = base_qs.none()
                else:
                    # Coordinador: ver comedores de sus duplas asignadas
                    base_qs = base_qs.filter(dupla_id__in=duplas_ids)
            elif is_dupla:
                # Técnico o Abogado: ver comedores donde está asignado
                from django.db.models import Exists, OuterRef

                dupla_abogado_subq = Dupla.objects.filter(
                    comedor=OuterRef("pk"), abogado=user
                )
                dupla_tecnico_subq = Dupla.objects.filter(
                    comedor=OuterRef("pk"), tecnico=user
                )
                base_qs = (
                    Comedor.objects.filter(
                        Exists(dupla_abogado_subq) | Exists(dupla_tecnico_subq)
                    )
                    .select_related(
                        "provincia",
                        "municipio",
                        "localidad",
                        "referente",
                        "tipocomedor",
                        "ultimo_estado__estado_general__estado_actividad",
                        "ultimo_estado__estado_general__estado_proceso",
                        "ultimo_estado__estado_general__estado_detalle",
                    )
                    .annotate(
                        estado_general=Coalesce(
                            "ultimo_estado__estado_general__estado_actividad__estado",
                            Value(Comedor.ESTADO_GENERAL_DEFAULT),
                        )
                    )
                    .values(
                        "id",
                        "nombre",
                        "estado_general",
                        "tipocomedor__nombre",
                        "organizacion__nombre",
                        "programa__nombre",
                        "dupla__nombre",
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
                        "ultimo_estado__estado_general__estado_actividad__estado",
                        "ultimo_estado__estado_general__estado_proceso",
                        "ultimo_estado__estado_general__estado_detalle",
                        "estado_validacion",
                        "fecha_validado",
                    )
                    .order_by("-id")
                )

        return COMEDOR_ADVANCED_FILTER.filter_queryset(base_qs, request_or_get)

    @staticmethod
    def get_comedor_detail_object(comedor_id: int):
        """Obtiene un comedor con todas sus relaciones optimizadas para la vista de detalle."""
        preload_valores_comida_cache()
        qs = Comedor.objects.select_related(
            "provincia",
            "municipio",
            "localidad",
            "referente",
            "organizacion",
            "programa",
            "tipocomedor",
            "dupla",
            "ultimo_estado__estado_general__estado_actividad",
            "ultimo_estado__estado_general__estado_proceso",
            "ultimo_estado__estado_general__estado_detalle",
        ).prefetch_related(
            "expedientes_pagos",
            Prefetch(
                "imagenes",
                queryset=ImagenComedor.objects.only("imagen"),
                to_attr="imagenes_optimized",
            ),
            Prefetch(
                "relevamiento_set",
                queryset=Relevamiento.objects.select_related(
                    "prestacion",
                    "colaboradores",
                    "colaboradores__cantidad_colaboradores",
                    "recursos",
                    "funcionamiento",
                    "funcionamiento__modalidad_prestacion",
                    "espacio",
                    "espacio__tipo_espacio_fisico",
                    "anexo",
                ).order_by("-fecha_visita", "-id"),
                to_attr="relevamientos_optimized",
            ),
            Prefetch(
                "observacion_set",
                queryset=Observacion.objects.order_by("-fecha_visita")[:3],
                to_attr="observaciones_optimized",
            ),
            Prefetch(
                "clasificacioncomedor_set",
                queryset=ClasificacionComedor.objects.select_related(
                    "categoria"
                ).order_by("-fecha"),
                to_attr="clasificaciones_optimized",
            ),
            Prefetch(
                "rendiciones_cuentas_mensuales",
                queryset=RendicionCuentaMensual.objects.only("id"),
                to_attr="rendiciones_optimized",
            ),
            Prefetch(
                "programa_changes",
                queryset=AuditComedorPrograma.objects.select_related(
                    "from_programa", "to_programa", "changed_by"
                ).order_by("-changed_at", "-id"),
                to_attr="programa_changes_optimized",
            ),
        )
        return get_object_or_404(qs, pk=comedor_id)

    @staticmethod
    def get_ubicaciones_ids(data):
        """Convierte nombres de ubicaciones a sus IDs correspondientes dentro de ``data``."""
        from core.models import (  # pylint: disable=import-outside-toplevel
            Provincia,
            Municipio,
            Localidad,
        )

        if "provincia" in data:
            data["provincia"] = get_id_by_nombre(Provincia, data["provincia"])
        if "municipio" in data:
            data["municipio"] = get_id_by_nombre(Municipio, data["municipio"])
        if "localidad" in data:
            data["localidad"] = get_id_by_nombre(Localidad, data["localidad"])
        return data

    @staticmethod
    def create_or_update_referente(data, referente_instance=None):
        """Crea o actualiza un ``Referente`` usando los datos provistos en ``data``."""
        referente_data = data.get("referente", {})
        referente_data["celular"] = normalize_field(referente_data.get("celular"), "-")
        referente_data["documento"] = normalize_field(
            referente_data.get("documento"), "."
        )
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
    def get_relevamiento_resumen(relevamientos):
        """Selecciona el relevamiento preferido para mostrar en el detalle."""
        if not relevamientos:
            return None
        estados_finalizados = {"Finalizado", "Finalizado/Excepciones"}
        for relevamiento in relevamientos:
            if getattr(relevamiento, "estado", None) in estados_finalizados:
                return relevamiento
        return relevamientos[0]

    @staticmethod
    def get_presupuestos(comedor_id: int, relevamientos_prefetched=None):
        valor_map = preload_valores_comida_cache()
        if relevamientos_prefetched:
            relevamiento = ComedorService.get_relevamiento_resumen(
                relevamientos_prefetched
            )
        else:
            relevamiento = (
                Relevamiento.objects.select_related("prestacion")
                .filter(
                    comedor=comedor_id,
                    estado__in=["Finalizado", "Finalizado/Excepciones"],
                )
                .order_by("-fecha_visita", "-id")
                .only("prestacion", "fecha_visita", "estado")
                .first()
            )
            if not relevamiento:
                relevamiento = (
                    Relevamiento.objects.select_related("prestacion")
                    .filter(comedor=comedor_id)
                    .order_by("-fecha_visita", "-id")
                    .only("prestacion", "fecha_visita")
                    .first()
                )
        count = {
            "desayuno": 0,
            "almuerzo": 0,
            "merienda": 0,
            "cena": 0,
        }
        if relevamiento and relevamiento.prestacion:
            # Obtener prestación del relevamiento
            prestacion = relevamiento.prestacion
            dias = [
                "lunes",
                "martes",
                "miercoles",
                "jueves",
                "viernes",
                "sabado",
                "domingo",
            ]
            tipos = [
                "desayuno",
                "almuerzo",
                "merienda",
                "cena",
                "merienda_reforzada",
            ]
            for tipo in tipos:
                count[tipo] = sum(
                    getattr(prestacion, f"{dia}_{tipo}_actual", 0) or 0 for dia in dias
                )
        count_beneficiarios = sum(count.values())
        total_almuerzo_cena = count["almuerzo"] + count["cena"]
        total_desayuno_merienda = (
            count["desayuno"] + count["merienda"] + count.get("merienda_reforzada", 0)
        )
        monto_prestacion_mensual = (
            total_almuerzo_cena * 763 + total_desayuno_merienda * 383
        )
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
            monto_prestacion_mensual,
        )

    @staticmethod
    def get_prestaciones_aprobadas_por_tipo(informe_tecnico):
        """Suma las prestaciones aprobadas por tipo en el informe tecnico."""
        if not informe_tecnico:
            return None
        dias = (
            "lunes",
            "martes",
            "miercoles",
            "jueves",
            "viernes",
            "sabado",
            "domingo",
        )
        tipos = ("desayuno", "almuerzo", "merienda", "cena")
        count = {tipo: 0 for tipo in tipos}
        for tipo in tipos:
            total = 0
            for dia in dias:
                value = getattr(informe_tecnico, f"aprobadas_{tipo}_{dia}", 0)
                if value is None:
                    continue
                try:
                    total += int(value)
                except (TypeError, ValueError):
                    continue
            count[tipo] = total
        return count

    @staticmethod
    def calcular_monto_prestacion_mensual_por_aprobadas(prestaciones_por_tipo):
        """Calcula el monto mensual usando prestaciones aprobadas."""
        if not prestaciones_por_tipo:
            return None
        total_almuerzo_cena = prestaciones_por_tipo.get(
            "almuerzo", 0
        ) + prestaciones_por_tipo.get("cena", 0)
        total_desayuno_merienda = prestaciones_por_tipo.get(
            "desayuno", 0
        ) + prestaciones_por_tipo.get("merienda", 0)
        return total_almuerzo_cena * 763 + total_desayuno_merienda * 383

    @staticmethod
    def get_nomina_detail(comedor_pk, page=1, per_page=100):
        qs_nomina = Nomina.objects.filter(comedor_id=comedor_pk).select_related(
            "ciudadano__sexo"
        )
        age_expr = TimestampDiffYears(F("ciudadano__fecha_nacimiento"), Now())
        qs_nomina_age = qs_nomina.annotate(edad=age_expr)
        resumen = qs_nomina_age.aggregate(
            cantidad_nomina_m=Count("id", filter=Q(ciudadano__sexo__sexo="Masculino")),
            cantidad_nomina_f=Count("id", filter=Q(ciudadano__sexo__sexo="Femenino")),
            cantidad_nomina_x=Count("id", filter=Q(ciudadano__sexo__sexo="X")),
            espera=Count("id", filter=Q(estado=Nomina.ESTADO_PENDIENTE)),
            cantidad_total=Count("id"),
            rango_ninos=Count(
                "id", filter=Q(edad__lte=13, estado=Nomina.ESTADO_ACTIVO)
            ),
            rango_adolescentes=Count(
                "id", filter=Q(edad__gte=14, edad__lte=17, estado=Nomina.ESTADO_ACTIVO)
            ),
            rango_adultos=Count(
                "id", filter=Q(edad__gte=18, edad__lte=49, estado=Nomina.ESTADO_ACTIVO)
            ),
            rango_adultos_mayores=Count(
                "id", filter=Q(edad__gte=50, edad__lte=65, estado=Nomina.ESTADO_ACTIVO)
            ),
            rango_adulto_mayor_avanzado=Count(
                "id", filter=Q(edad__gte=66, estado=Nomina.ESTADO_ACTIVO)
            ),
            rango_total_activos=Count(
                "id",
                filter=Q(
                    estado=Nomina.ESTADO_ACTIVO,
                    ciudadano__fecha_nacimiento__isnull=False,
                ),
            ),
        )
        total_activos = resumen["rango_total_activos"] or 0

        def _pct(value):
            if not total_activos:
                return 0
            return int(round((value or 0) * 100 / total_activos))

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
            resumen["cantidad_nomina_x"],
            resumen["espera"],
            resumen["cantidad_total"],
            {
                "ninos": resumen["rango_ninos"],
                "adolescentes": resumen["rango_adolescentes"],
                "adultos": resumen["rango_adultos"],
                "adultos_mayores": resumen["rango_adultos_mayores"],
                "adulto_mayor_avanzado": resumen["rango_adulto_mayor_avanzado"],
                "total_activos": total_activos,
                "pct_ninos": _pct(resumen["rango_ninos"]),
                "pct_adolescentes": _pct(resumen["rango_adolescentes"]),
                "pct_adultos": _pct(resumen["rango_adultos"]),
                "pct_adultos_mayores": _pct(resumen["rango_adultos_mayores"]),
                "pct_adulto_mayor_avanzado": _pct(
                    resumen["rango_adulto_mayor_avanzado"]
                ),
            },
        )

    @staticmethod
    def post_comedor_relevamiento(request, comedor):
        is_new_relevamiento = "territorial" in request.POST
        is_edit_relevamiento = "territorial_editar" in request.POST
        if is_new_relevamiento or is_edit_relevamiento:
            try:
                relevamiento = None
                if is_new_relevamiento:
                    relevamiento = RelevamientoService.create_pendiente(
                        request, comedor.id
                    )
                elif is_edit_relevamiento:
                    relevamiento = RelevamientoService.update_territorial(request)
                if not relevamiento or not getattr(relevamiento, "comedor", None):
                    messages.error(
                        request,
                        "Error al crear o editar el relevamiento: No se pudo obtener el relevamiento o su comedor.",
                    )
                    return redirect("comedor_detalle", pk=comedor.id)
                return redirect(
                    reverse(
                        "relevamiento_detalle",
                        kwargs={
                            "pk": relevamiento.pk,
                            "comedor_pk": relevamiento.comedor.pk,
                        },
                    )
                )
            except Exception as e:
                messages.error(request, f"Error al crear el relevamiento: {e}")
                return redirect("comedor_detalle", pk=comedor.id)
        else:
            return redirect("comedor_detalle", pk=comedor.id)

    @staticmethod
    def buscar_ciudadanos_por_documento(query, max_results=10):
        return list(Ciudadano.buscar_por_documento(query, max_results=max_results))

    @staticmethod
    def _parse_fecha_renaper(fecha_raw):
        if not fecha_raw:
            return None
        if isinstance(fecha_raw, date):
            return fecha_raw
        if isinstance(fecha_raw, datetime):
            return fecha_raw.date()

        value = str(fecha_raw).strip()
        formatos = ("%Y-%m-%d", "%d/%m/%Y", "%Y%m%d")
        for fmt in formatos:
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue

        try:
            value_iso = value.replace("Z", "")
            return datetime.fromisoformat(value_iso).date()
        except ValueError:
            logger.warning("No se pudo parsear fecha de nacimiento RENAPER: %s", value)
            return None

    @staticmethod
    def _replace_number_words(text):
        """Convierte palabras de números al comienzo del string a dígitos."""
        if not text:
            return ""
        numbers = {
            "uno": "1",
            "una": "1",
            "dos": "2",
            "tres": "3",
            "cuatro": "4",
            "cinco": "5",
            "seis": "6",
            "siete": "7",
            "ocho": "8",
            "nueve": "9",
            "diez": "10",
            "once": "11",
            "doce": "12",
            "trece": "13",
            "catorce": "14",
            "quince": "15",
            "dieciseis": "16",
            "dieciséis": "16",
            "diecisiete": "17",
            "dieciocho": "18",
            "diecinueve": "19",
            "veinte": "20",
            "veintiuno": "21",
            "veintidos": "22",
            "veintidós": "22",
            "veintitres": "23",
            "veintitrés": "23",
            "veinticuatro": "24",
            "veinticinco": "25",
            "veintiseis": "26",
            "veintiséis": "26",
            "veintisiete": "27",
            "veintiocho": "28",
            "veintinueve": "29",
            "treinta": "30",
        }
        parts = text.split()
        if parts and parts[0] in numbers:
            parts[0] = numbers[parts[0]]
        return " ".join(parts)

    @staticmethod
    def _to_camel_case(value):
        """Normaliza espacios y aplica Title Case básico."""
        if not value:
            return ""
        normalized = " ".join(str(value).strip().split())
        return normalized.title()

    @staticmethod
    def _apply_geo_alias(value):
        """Reemplaza alias conocidos de nombres geográficos."""
        if not value:
            return ""
        alias_map = {
            "ciudad de buenos aires": "ciudad autonoma de buenos aires",
            "ciudad autonoma de buenos aires": "ciudad autonoma de buenos aires",
            "caba": "ciudad autonoma de buenos aires",
            "capital federal": "ciudad autonoma de buenos aires",
        }
        text = str(value).replace("_", " ").replace("-", " ").lower()
        text = " ".join(text.split())
        return alias_map.get(text, value)

    @staticmethod
    def _normalize_geo_value(value):
        """Normaliza nombres geográficos para comparación contra base local."""
        if not value:
            return ""
        text = ComedorService._apply_geo_alias(value)
        text = str(text)
        text = text.replace("_", " ").replace("-", " ").lower()
        text = (
            unicodedata.normalize("NFKD", text)
            .encode("ascii", "ignore")
            .decode("utf-8")
        )
        text = " ".join(text.split())
        return ComedorService._replace_number_words(text)

    @staticmethod
    def _normalize_text(value):
        if not value:
            return ""
        text = str(value)
        text = text.replace("_", " ").replace("-", " ").lower()
        text = (
            unicodedata.normalize("NFKD", text)
            .encode("ascii", "ignore")
            .decode("utf-8")
        )
        return " ".join(text.split())

    @staticmethod
    def _match_geo_by_name(queryset, valor_api):
        """
        Busca coincidencia exacta por nombre normalizado en un queryset pequeño
        (provincias/municipios/localidades).
        """
        objetivo = ComedorService._normalize_geo_value(valor_api)
        if not objetivo:
            return None
        for obj in queryset:
            if (
                ComedorService._normalize_geo_value(getattr(obj, "nombre", ""))
                == objetivo
            ):
                return obj
        return None

    @staticmethod
    def _mapear_ubicacion_desde_renaper(datos):
        """
        Mapea provincia, municipio y localidad devolviendo instancias locales.
        Usa coincidencia por nombre normalizado y un reemplazo básico de números.
        """
        provincia_api = datos.get("provincia_api")
        municipio_api = datos.get("municipio_api")
        localidad_api = datos.get("localidad_api")

        provincia_obj = None
        municipio_obj = None
        localidad_obj = None

        if provincia_api:
            provincia_obj = ComedorService._match_geo_by_name(
                Provincia.objects.all(), provincia_api
            )

        if municipio_api:
            municipio_qs = Municipio.objects.all()
            if provincia_obj:
                municipio_qs = municipio_qs.filter(provincia=provincia_obj)
            municipio_obj = ComedorService._match_geo_by_name(
                municipio_qs, municipio_api
            )

        if localidad_api:
            localidad_qs = Localidad.objects.all()
            if municipio_obj:
                localidad_qs = localidad_qs.filter(municipio=municipio_obj)
            elif provincia_obj:
                localidad_qs = localidad_qs.filter(municipio__provincia=provincia_obj)
            localidad_obj = ComedorService._match_geo_by_name(
                localidad_qs, localidad_api
            )

        return {
            "provincia": provincia_obj,
            "municipio": municipio_obj,
            "localidad": localidad_obj,
        }

    @staticmethod
    def _match_nacionalidad(valor_api):
        objetivo = ComedorService._normalize_text(valor_api)
        if not objetivo:
            return None
        for nacionalidad in Nacionalidad.objects.all():
            if ComedorService._normalize_text(nacionalidad.nacionalidad) == objetivo:
                return nacionalidad
        return None

    @staticmethod
    def _consultar_renaper_por_dni(dni):
        """
        Consulta RENAPER probando con los sexos disponibles porque el formulario
        de búsqueda no solicita el dato.
        """
        last_error = None
        for sexo in ("M", "F", "X"):
            resultado = consultar_datos_renaper(dni, sexo)
            if resultado.get("success"):
                return resultado
            last_error = resultado.get("error") or last_error
        return {
            "success": False,
            "error": last_error or "No se encontraron datos en RENAPER.",
        }

    @staticmethod
    def _build_ciudadano_data_from_renaper(datos, dni_str):
        """Mapea datos de RENAPER a campos de Ciudadano."""
        apellido = ComedorService._to_camel_case(datos.get("apellido"))
        nombre = ComedorService._to_camel_case(datos.get("nombre"))
        fecha_nacimiento = ComedorService._parse_fecha_renaper(
            datos.get("fecha_nacimiento")
        )

        if not apellido or not nombre or not fecha_nacimiento:
            return (
                None,
                "RENAPER no devolvió datos mínimos para crear el ciudadano.",
            )

        try:
            documento_valor = int(datos.get("dni") or dni_str)
        except (TypeError, ValueError):
            return (None, "RENAPER devolvió un DNI inválido.")

        ciudadano_data = {
            "apellido": apellido,
            "nombre": nombre,
            "documento": documento_valor,
            "tipo_documento": datos.get("tipo_documento") or Ciudadano.DOCUMENTO_DNI,
            "fecha_nacimiento": fecha_nacimiento,
            "origen_dato": "renaper",
        }

        if datos.get("sexo"):
            ciudadano_data["sexo"] = datos["sexo"]

        # Datos de contacto básicos desde RENAPER
        ciudadano_data.update(
            {
                "calle": datos.get("calle") or None,
                "altura": str(datos.get("altura")) if datos.get("altura") else None,
                "piso_departamento": datos.get("piso_vivienda")
                or datos.get("departamento_vivienda"),
                "barrio": datos.get("barrio") or None,
                "codigo_postal": (
                    str(datos.get("codigo_postal"))
                    if datos.get("codigo_postal")
                    else None
                ),
            }
        )

        ubicacion = ComedorService._mapear_ubicacion_desde_renaper(datos)
        if ubicacion["provincia"]:
            ciudadano_data["provincia"] = ubicacion["provincia"].pk
        if ubicacion["municipio"]:
            ciudadano_data["municipio"] = ubicacion["municipio"].pk
        if ubicacion["localidad"]:
            ciudadano_data["localidad"] = ubicacion["localidad"].pk

        nacionalidad_obj = ComedorService._match_nacionalidad(
            datos.get("nacionalidad_api")
        )
        if nacionalidad_obj:
            ciudadano_data["nacionalidad"] = nacionalidad_obj.pk

        return (ciudadano_data, None)

    @staticmethod
    def obtener_datos_ciudadano_desde_renaper(dni, sexo=None):
        """
        Consulta RENAPER y devuelve datos listos para precargar un formulario.
        """
        dni_str = str(dni or "").strip()
        if not dni_str.isdigit() or len(dni_str) < 7:
            return {
                "success": False,
                "message": "Ingrese un DNI numérico válido para consultar RENAPER.",
            }

        sexo_value = (sexo or "").upper()
        if sexo_value in ("M", "F", "X"):
            resultado = consultar_datos_renaper(dni_str, sexo_value)
        else:
            resultado = ComedorService._consultar_renaper_por_dni(dni_str)

        if not resultado.get("success"):
            return {
                "success": False,
                "message": resultado.get(
                    "error", "No se encontraron datos en RENAPER."
                ),
            }

        ciudadano_data, error = ComedorService._build_ciudadano_data_from_renaper(
            resultado.get("data") or {}, dni_str
        )
        if not ciudadano_data:
            return {"success": False, "message": error}

        return {
            "success": True,
            "data": ciudadano_data,
            "message": "Datos obtenidos desde RENAPER.",
            "datos_api": resultado.get("datos_api"),
        }

    @staticmethod
    def crear_ciudadano_desde_renaper(dni, user=None):
        """
        Intenta crear un ciudadano a partir de una consulta a RENAPER.
        Si ya existe, devuelve el registro actual sin crearlo nuevamente.
        """
        dni_str = str(dni or "").strip()
        if not dni_str.isdigit() or len(dni_str) < 7:
            return {
                "success": False,
                "message": "Ingrese un DNI numérico válido para consultar RENAPER.",
            }

        existente = Ciudadano.objects.filter(
            tipo_documento=Ciudadano.DOCUMENTO_DNI, documento=int(dni_str)
        ).first()
        if existente:
            return {
                "success": True,
                "ciudadano": existente,
                "created": False,
                "message": "El ciudadano ya existe en la base.",
            }

        resultado = ComedorService.obtener_datos_ciudadano_desde_renaper(dni_str)
        if not resultado.get("success"):
            return {
                "success": False,
                "message": resultado.get(
                    "message", "No se encontraron datos en RENAPER."
                ),
            }

        ciudadano_data = dict(resultado.get("data") or {})

        if user and getattr(user, "is_authenticated", False):
            ciudadano_data["creado_por"] = user
            ciudadano_data["modificado_por"] = user

        try:
            ciudadano = Ciudadano.objects.create(**ciudadano_data)
        except Exception:
            logger.exception(
                "No se pudo crear ciudadano desde RENAPER",
                extra={"dni": dni_str, "datos": ciudadano_data},
            )
            return {
                "success": False,
                "message": "No se pudo crear el ciudadano con los datos de RENAPER.",
            }

        return {
            "success": True,
            "ciudadano": ciudadano,
            "created": True,
            "message": "Ciudadano creado automáticamente con datos de RENAPER.",
            "datos_api": resultado.get("datos_api"),
        }

    @staticmethod
    def agregar_ciudadano_a_nomina(
        comedor_id, ciudadano_id, user, estado=None, observaciones=None
    ):
        ciudadano = get_object_or_404(Ciudadano, pk=ciudadano_id)

        if Nomina.objects.filter(ciudadano=ciudadano, comedor_id=comedor_id).exists():
            return False, "Esta persona ya está en la nómina."

        try:
            with transaction.atomic():
                Nomina.objects.create(
                    ciudadano=ciudadano,
                    comedor_id=comedor_id,
                    estado=estado or Nomina.ESTADO_PENDIENTE,
                    observaciones=observaciones,
                )

            return True, "Persona añadida correctamente a la nómina."
        except Exception as e:
            return False, f"Ocurrió un error al agregar a la nómina: {e}"

    @staticmethod
    @transaction.atomic
    def crear_ciudadano_y_agregar_a_nomina(
        ciudadano_data, comedor_id, user, estado, observaciones
    ):
        """
        Crea un ciudadano nuevo y lo agrega a la nómina con estado y observaciones.
        ciudadano_data: dict con datos para crear ciudadano (ej: datos validados del form).
        """
        ciudadano = Ciudadano.objects.create(**ciudadano_data)

        ok, msg = ComedorService.agregar_ciudadano_a_nomina(
            comedor_id=comedor_id,
            ciudadano_id=ciudadano.id,
            user=user,
            estado=estado,
            observaciones=observaciones,
        )
        if not ok:
            ciudadano.delete()
        return ok, msg

    @staticmethod
    def crear_admision_desde_comedor(request, comedor):
        """
        Crea una nueva admisión asociada al comedor actual.

        Regla:
        - Solo puede haber una admisión de tipo 'incorporacion' por comedor.
        - Puede haber hasta 4 admisiones de tipo 'renovacion' activas.
        Luego redirige nuevamente al detalle del comedor.
        """

        tipo_admision = request.POST.get("admision")

        if not tipo_admision:
            messages.error(request, "Debe seleccionar un tipo de admisión.")
            return redirect("comedor_detalle", pk=comedor.pk)

        if (
            tipo_admision == "renovacion"
            and not Admision.objects.filter(
                comedor=comedor, tipo="incorporacion"
            ).exists()
        ):
            messages.error(
                request,
                "No se puede crear una admisión de Renovación sin una Incorporación previa. "
                "Debe existir al menos una admisión de Incorporación para este comedor, "
                "independientemente de su estado.",
            )
            return redirect("comedor_detalle", pk=comedor.pk)

        if tipo_admision == "incorporacion":
            if Admision.objects.filter(
                comedor=comedor, tipo="incorporacion", activa=True
            ).exists():
                messages.warning(
                    request,
                    "Ya existe una admision de Incorporacion activa para este comedor.",
                )
                return redirect("comedor_detalle", pk=comedor.pk)
        else:
            renovaciones_activas = Admision.objects.filter(
                comedor=comedor, tipo="renovacion", activa=True
            ).count()
            if renovaciones_activas >= 4:
                messages.warning(
                    request,
                    "Ya existen 4 admisiones de Renovacion activas para este comedor.",
                )
                return safe_redirect(
                    request,
                    default=reverse("comedor_detalle", kwargs={"pk": comedor.pk}),
                    target=request.path,
                )

        nueva_admision = Admision.objects.create(
            comedor=comedor,
            tipo=tipo_admision,
        )
        if Hitos.objects.filter(comedor=comedor).exists():
            messages.info(
                request,
                "El comedor ya tiene hitos registrados.",
            )
        else:
            Hitos.objects.create(comedor=comedor)
        messages.success(
            request,
            f"Se creó una nueva admisión de tipo '{nueva_admision.get_tipo_display()}' correctamente.",
        )

        messages.success(
            request,
            f"Se creó una nuevo hito correctamente.",
        )

        # 🔁 Redirigir al mismo comedor
        return redirect("comedor_detalle", pk=comedor.pk)
