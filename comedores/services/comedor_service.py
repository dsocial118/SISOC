import re
import json
import logging
from typing import Union, Any, Dict, List, Tuple

from django.db.models import Q, Count, Prefetch, QuerySet
from django.db import transaction
from django.core.paginator import Paginator
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.shortcuts import get_object_or_404

from relevamientos.models import Relevamiento, ClasificacionComedor
from relevamientos.service import RelevamientoService
from ciudadanos.models import Ciudadano, HistorialCiudadanoProgramas, CiudadanoPrograma
from comedores.forms.comedor_form import ImagenComedorForm
from comedores.models import Comedor, ImagenComedor, Nomina, Observacion, Referente
from comedores.utils import (
    get_object_by_filter,
    get_id_by_nombre,
    normalize_field,
    preload_valores_comida_cache,
)

from admisiones.models.admisiones import Admision
from rendicioncuentasmensual.models import RendicionCuentaMensual
from intervenciones.models.intervenciones import Intervencion

logger = logging.getLogger("django")

from comedores.services.filter_config import FIELD_MAP, FIELD_TYPES, TEXT_OPS, NUM_OPS


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
            if comedor_instance.foto_legajo:
                try:
                    comedor_instance.foto_legajo.delete(save=False)
                except Exception:
                    logger.exception(
                        "Error al eliminar la foto de legajo del comedor %s",
                        comedor_instance.pk,
                    )
            comedor_instance.foto_legajo = None
            comedor_instance.save(update_fields=["foto_legajo"])

    @staticmethod
    def get_filtered_comedores(request_or_get: Any) -> QuerySet:
        """
        Filtra comedores a partir de un único parámetro GET `filters` (JSON URL-encoded).

        Estructura esperada:
            {
              "logic": "AND" | "OR",                # combinación global (default AND)
              "items": [
                {"field": str, "op": str, "value": Any, "empty_mode": "both|null|blank"}
              ]
            }

        - Items del MISMO `field` se combinan con OR.
        - Resultados por campo se combinan con `logic` global (AND/OR).
        - Valida por whitelist (FIELD_MAP, TEXT_OPS/NUM_OPS) y castea números de forma segura.
        - Items inválidos se ignoran con tolerancia a errores.
        - Devuelve un QuerySet con `.values(...)` optimizado para listado.
        """

        def _coerce_value(field: str, value: Any) -> Tuple[bool, Any]:
            """Cast seguro según tipo de campo. Devuelve (ok, valor_cast)."""
            ftype = FIELD_TYPES.get(field)
            if ftype == "number":
                try:
                    if field in {"latitud", "longitud"}:
                        return True, float(value)
                    # enteros
                    return True, int(value)
                except (TypeError, ValueError):
                    return False, None
            # texto
            return True, value

        def _build_q_for_item(item: Dict[str, Any]) -> Union[Q, None]:
            """Construye el Q() para un item de filtro.

            - Valida field/op en whitelist.
            - Maneja operador `empty` con `empty_mode` y tipos de campo.
            - Aplica negación para `ne` y `ncontains` invirtiendo el Q.
            - Ignora valores faltantes/strings vacíos.
            """
            field = item.get("field")
            op = item.get("op")
            if not field or field not in FIELD_MAP:
                return None
            mapped = FIELD_MAP[field]
            ftype = FIELD_TYPES.get(field)
            if ftype == "text" and op not in TEXT_OPS:
                return None
            if ftype == "number" and op not in NUM_OPS:
                return None

            # Operador empty no usa value
            if op == "empty":
                empty_mode = (item.get("empty_mode") or "both").lower()
                # isnull aplica siempre; exact="" solo a campos de texto.
                null_q = Q(**{f"{mapped}__isnull": True})
                if ftype == "text":
                    blank_q = Q(**{f"{mapped}__exact": ""})
                    if empty_mode == "null":
                        return null_q
                    if empty_mode == "blank":
                        return blank_q
                    # both (default)
                    return null_q | blank_q
                # Para numéricos blank no aplica
                return null_q

            # Para otros operadores, validar y castear valor
            value = item.get("value")
            if value is None or (isinstance(value, str) and value.strip() == ""):
                return None
            ok, casted = _coerce_value(field, value)
            if not ok:
                return None

            lookup = None
            negate = False
            if ftype == "text":
                if op == "eq":
                    lookup = f"{mapped}__iexact"
                elif op == "ne":
                    lookup = f"{mapped}__iexact"
                    negate = True
                elif op == "contains":
                    lookup = f"{mapped}__icontains"
                elif op == "ncontains":
                    lookup = f"{mapped}__icontains"
                    negate = True
            else:  # number
                if op == "eq":
                    lookup = f"{mapped}__exact"
                elif op == "ne":
                    lookup = f"{mapped}__exact"
                    negate = True
                elif op == "gt":
                    lookup = f"{mapped}__gt"
                elif op == "lt":
                    lookup = f"{mapped}__lt"

            if not lookup:
                return None
            q = Q(**{lookup: casted})
            return ~q if negate else q

        # Base queryset (sin filtros si `filters` inválido/ausente).
        base_qs = (
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

        # Obtener filters desde request o QueryDict de forma robusta
        try:
            get_params = (
                request_or_get.GET if hasattr(request_or_get, "GET") else request_or_get
            )
        except Exception:
            get_params = {}

        filters_raw = None
        if isinstance(get_params, dict):
            filters_raw = get_params.get("filters")
        else:
            try:
                filters_raw = get_params.get("filters")
            except Exception:
                filters_raw = None

        if not filters_raw:
            return base_qs

        try:
            payload = json.loads(filters_raw)
        except (json.JSONDecodeError, TypeError):
            return base_qs

        items = payload.get("items") or []
        if not isinstance(items, list) or len(items) == 0:
            return base_qs

        # Agrupar por field
        groups: Dict[str, List[Q]] = {}
        for it in items:
            if not isinstance(it, dict):
                continue
            q = _build_q_for_item(it)
            if q is None:
                continue
            field = it.get("field")
            groups.setdefault(field, []).append(q)

        if not groups:
            return base_qs

        # Combinar grupos: mismo campo con OR; entre campos según lógica global.
        logic = str(payload.get("logic") or "AND").upper()
        logic = "OR" if logic == "OR" else "AND"

        # Q final
        final_q: Union[Q, None] = None
        for qlist in groups.values():
            if not qlist:
                continue
            group_q = qlist[0]
            for subq in qlist[1:]:
                group_q = group_q | subq

            if final_q is None:
                final_q = group_q
            else:
                final_q = (final_q | group_q) if logic == "OR" else (final_q & group_q)

        if final_q is None:
            return base_qs

        return base_qs.filter(final_q)

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
        ).prefetch_related(
            "expedientes_pagos",
            Prefetch(
                "imagenes",
                queryset=ImagenComedor.objects.only("imagen"),
                to_attr="imagenes_optimized",
            ),
            Prefetch(
                "relevamiento_set",
                queryset=Relevamiento.objects.select_related("prestacion").order_by(
                    "-estado", "-id"
                ),
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
                "admision_set",
                queryset=Admision.objects.select_related("tipo_convenio", "estado"),
                to_attr="admisiones_optimized",
            ),
            Prefetch(
                "rendiciones_cuentas_mensuales",
                queryset=RendicionCuentaMensual.objects.only("id"),
                to_attr="rendiciones_optimized",
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
    def get_presupuestos(comedor_id: int, relevamientos_prefetched=None):
        valor_map = preload_valores_comida_cache()
        if relevamientos_prefetched:
            relevamiento = relevamientos_prefetched[0]
        else:
            relevamiento = (
                Relevamiento.objects.select_related("prestacion")
                .filter(comedor=comedor_id)
                .order_by("-fecha_visita")
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
    def get_nomina_detail(comedor_pk, page=1, per_page=100):
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
        cleaned = (query or "").strip()
        if len(cleaned) < 4 or not cleaned.isdigit():
            return []
        return list(
            Ciudadano.objects.filter(documento__startswith=cleaned)
            .only("id", "nombre", "apellido", "documento")
            .order_by("documento")[:max_results]
        )

    @staticmethod
    def agregar_ciudadano_a_nomina(
        comedor_id, ciudadano_id, user, estado_id=None, observaciones=None
    ):
        ciudadano = get_object_or_404(Ciudadano, pk=ciudadano_id)

        if Nomina.objects.filter(ciudadano=ciudadano, comedor_id=comedor_id).exists():
            return False, "Esta persona ya está en la nómina."

        try:
            with transaction.atomic():
                Nomina.objects.create(
                    ciudadano=ciudadano,
                    comedor_id=comedor_id,
                    estado_id=estado_id or None,
                    observaciones=observaciones,
                )

                _ciudadano_programa, created = CiudadanoPrograma.objects.get_or_create(
                    ciudadano=ciudadano,
                    programas_id=2,
                    defaults={"creado_por": user},
                )
                if created:
                    HistorialCiudadanoProgramas.objects.create(
                        programa_id=2,
                        ciudadano=ciudadano,
                        accion="agregado",
                        usuario=user,
                    )

            return True, "Persona añadida correctamente a la nómina."
        except Exception as e:
            return False, f"Ocurrió un error al agregar a la nómina: {e}"

    @staticmethod
    @transaction.atomic
    def crear_ciudadano_y_agregar_a_nomina(
        ciudadano_data, comedor_id, user, estado_id, observaciones
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
            estado_id=estado_id,
            observaciones=observaciones,
        )
        if not ok:
            ciudadano.delete()
        return ok, msg
