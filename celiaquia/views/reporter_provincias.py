from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator
from django.db.models import Count
from django.db.models.functions import TruncMonth
from django.views.generic import TemplateView

from core.models import Provincia
from celiaquia.models import (
    EstadoCupo,
    ExpedienteCiudadano,
    ResultadoSintys,
    RevisionTecnico,
)


PAGE_SIZE = 12
MONTH_NAMES = (
    "Ene",
    "Feb",
    "Mar",
    "Abr",
    "May",
    "Jun",
    "Jul",
    "Ago",
    "Sep",
    "Oct",
    "Nov",
    "Dic",
)

VALIDACION_ITEMS = (
    {"code": RevisionTecnico.PENDIENTE, "label": "Pendiente", "tone": "neutral"},
    {"code": RevisionTecnico.APROBADO, "label": "Aprobado", "tone": "success"},
    {"code": RevisionTecnico.RECHAZADO, "label": "Rechazado", "tone": "danger"},
    {"code": RevisionTecnico.SUBSANAR, "label": "Subsanar", "tone": "warning"},
    {"code": RevisionTecnico.SUBSANADO, "label": "Subsanado", "tone": "accent"},
)
SINTYS_ITEMS = (
    {"code": ResultadoSintys.SIN_CRUCE, "label": "Sin cruce", "tone": "neutral"},
    {"code": ResultadoSintys.MATCH, "label": "Match", "tone": "success"},
    {"code": ResultadoSintys.NO_MATCH, "label": "No match", "tone": "danger"},
)
CUPO_ITEMS = (
    {"code": EstadoCupo.NO_EVAL, "label": "No evaluado", "tone": "neutral"},
    {"code": EstadoCupo.DENTRO, "label": "Dentro de cupo", "tone": "success"},
    {"code": EstadoCupo.FUERA, "label": "Fuera de cupo", "tone": "danger"},
)


def _safe_profile(user):
    try:
        return user.profile
    except (AttributeError, ObjectDoesNotExist):
        return None


def _is_provincial(user) -> bool:
    profile = _safe_profile(user)
    return bool(profile and profile.es_usuario_provincial and profile.provincia_id)


def _percentage(value, total):
    return round((value / total) * 100, 1) if total else 0


def _format_percentage(value, total):
    return f"{_percentage(value, total):.1f}".replace(".", ",") + "%"


def _group_counts(queryset, field_name):
    return [
        {"code": item[field_name], "total": item["total"]}
        for item in queryset.values(field_name).annotate(total=Count("id")).order_by()
    ]


def _build_status_items(grouped_counts, definitions, total_cases):
    totals_by_code = {item["code"]: item["total"] for item in grouped_counts}
    max_count = max(totals_by_code.values(), default=0)
    items = []

    for definition in definitions:
        count = totals_by_code.get(definition["code"], 0)
        items.append(
            {
                **definition,
                "count": count,
                "percentage": _percentage(count, total_cases),
                "size": round(count / max_count, 4) if max_count else 0,
            }
        )

    return items


def _build_metric(label, value, support, tone="base"):
    return {
        "label": label,
        "value": value,
        "support": support,
        "tone": tone,
    }


def _clean_query_params(query_params):
    cleaned = query_params.copy()

    for key in list(cleaned.keys()):
        values = [value for value in cleaned.getlist(key) if value]

        if values:
            cleaned.setlist(key, values)
        else:
            cleaned.pop(key, None)

    return cleaned


def _find_definition_label(code, definitions):
    for definition in definitions:
        if definition["code"] == code:
            return definition["label"]
    return code


def _build_province_breakdown(queryset, total_cases):
    grouped = list(
        queryset.values(
            "expediente__usuario_provincia__profile__provincia__id",
            "expediente__usuario_provincia__profile__provincia__nombre",
        )
        .annotate(total_expedientes=Count("expediente", distinct=True), total_casos=Count("id"))
        .order_by("-total_casos", "expediente__usuario_provincia__profile__provincia__nombre")
    )
    max_cases = max((item["total_casos"] for item in grouped), default=0)
    items = []

    for item in grouped:
        casos = item["total_casos"]
        items.append(
            {
                "provincia_id": item[
                    "expediente__usuario_provincia__profile__provincia__id"
                ],
                "nombre": item[
                    "expediente__usuario_provincia__profile__provincia__nombre"
                ]
                or "Sin provincia",
                "casos": casos,
                "expedientes": item["total_expedientes"],
                "share": _percentage(casos, total_cases),
                "size": round(casos / max_cases, 4) if max_cases else 0,
            }
        )

    return items


def _month_label(period):
    if not period:
        return ""
    return f"{MONTH_NAMES[period.month - 1]} {period.year}"


def _build_monthly_trend(queryset):
    grouped = list(
        queryset.annotate(periodo=TruncMonth("creado_en"))
        .values("periodo")
        .annotate(total=Count("id"))
        .order_by("-periodo")[:6]
    )
    grouped.reverse()
    max_total = max((item["total"] for item in grouped), default=0)

    return [
        {
            "label": _month_label(item["periodo"]),
            "count": item["total"],
            "size": round(item["total"] / max_total, 4) if max_total else 0,
        }
        for item in grouped
    ]


class ReporterProvinciasView(LoginRequiredMixin, TemplateView):
    template_name = "celiaquia/reporter_provincias.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        es_usuario_provincial = _is_provincial(user)
        profile = _safe_profile(user)
        provincia_usuario = profile.provincia if es_usuario_provincial else None

        provincia_id = self.request.GET.get("provincia") or ""

        if es_usuario_provincial and provincia_usuario:
            provincia_id = str(provincia_usuario.id)

        fecha_desde = self.request.GET.get("fecha_desde")
        fecha_hasta = self.request.GET.get("fecha_hasta")
        expediente_numero = self.request.GET.get("expediente_numero")
        documento_persona = self.request.GET.get("documento_persona")
        revision_tecnico = self.request.GET.get("revision_tecnico")
        resultado_sintys = self.request.GET.get("resultado_sintys")
        estado_cupo = self.request.GET.get("estado_cupo")

        queryset = ExpedienteCiudadano.objects.select_related(
            "expediente__usuario_provincia__profile__provincia",
            "ciudadano",
            "estado",
        )

        if provincia_id:
            queryset = queryset.filter(
                expediente__usuario_provincia__profile__provincia_id=provincia_id
            )

        if fecha_desde:
            queryset = queryset.filter(creado_en__gte=fecha_desde)

        if fecha_hasta:
            queryset = queryset.filter(creado_en__lte=fecha_hasta)

        if expediente_numero:
            queryset = queryset.filter(
                expediente__numero_expediente__icontains=expediente_numero
            )

        if documento_persona:
            queryset = queryset.filter(
                ciudadano__documento__icontains=documento_persona
            )

        if revision_tecnico:
            queryset = queryset.filter(revision_tecnico=revision_tecnico)

        if resultado_sintys:
            queryset = queryset.filter(resultado_sintys=resultado_sintys)

        if estado_cupo:
            queryset = queryset.filter(estado_cupo=estado_cupo)

        total_casos = queryset.count()
        stats_validacion = _group_counts(queryset, "revision_tecnico")
        stats_sintys = _group_counts(queryset, "resultado_sintys")
        stats_cupo = _group_counts(queryset, "estado_cupo")

        resumen_validacion = _build_status_items(
            stats_validacion,
            VALIDACION_ITEMS,
            total_casos,
        )
        resumen_sintys = _build_status_items(stats_sintys, SINTYS_ITEMS, total_casos)
        resumen_cupo = _build_status_items(stats_cupo, CUPO_ITEMS, total_casos)

        validacion_lookup = {item["code"]: item["count"] for item in resumen_validacion}
        sintys_lookup = {item["code"]: item["count"] for item in resumen_sintys}
        cupo_lookup = {item["code"]: item["count"] for item in resumen_cupo}

        casos_por_instancia = {
            "validacion_tecnica": {
                "pendiente": validacion_lookup.get(RevisionTecnico.PENDIENTE, 0),
                "aprobado": validacion_lookup.get(RevisionTecnico.APROBADO, 0),
                "rechazado": validacion_lookup.get(RevisionTecnico.RECHAZADO, 0),
                "subsanar": validacion_lookup.get(RevisionTecnico.SUBSANAR, 0),
                "subsanado": validacion_lookup.get(RevisionTecnico.SUBSANADO, 0),
            },
            "sintys": {
                "sin_cruce": sintys_lookup.get(ResultadoSintys.SIN_CRUCE, 0),
                "match": sintys_lookup.get(ResultadoSintys.MATCH, 0),
                "no_match": sintys_lookup.get(ResultadoSintys.NO_MATCH, 0),
            },
            "cupo": {
                "no_eval": cupo_lookup.get(EstadoCupo.NO_EVAL, 0),
                "dentro": cupo_lookup.get(EstadoCupo.DENTRO, 0),
                "fuera": cupo_lookup.get(EstadoCupo.FUERA, 0),
            },
        }

        casos_documentos_ok = queryset.filter(archivos_ok=True).count()
        casos_documentos_incompletos = total_casos - casos_documentos_ok
        porcentaje_documentos_ok = _percentage(casos_documentos_ok, total_casos)
        porcentaje_documentos_incompletos = _percentage(
            casos_documentos_incompletos,
            total_casos,
        )

        casos_con_comentarios = (
            queryset.filter(historial_comentarios__isnull=False)
            .values("id")
            .distinct()
            .count()
        )
        expedientes_por_provincia = _build_province_breakdown(queryset, total_casos)
        tendencia_mensual = _build_monthly_trend(queryset)
        metricas_principales = [
            _build_metric(
                "Casos analizados",
                total_casos,
                "Base filtrada del reporter",
                tone="base",
            ),
            _build_metric(
                "Aprobación técnica",
                _format_percentage(
                    casos_por_instancia["validacion_tecnica"]["aprobado"],
                    total_casos,
                ),
                f"{casos_por_instancia['validacion_tecnica']['aprobado']} legajos aprobados",
                tone="success",
            ),
            _build_metric(
                "Documentación completa",
                _format_percentage(casos_documentos_ok, total_casos),
                f"{casos_documentos_ok} casos con legajo completo",
                tone="accent",
            ),
            _build_metric(
                "Cruces con match",
                _format_percentage(casos_por_instancia["sintys"]["match"], total_casos),
                f"{casos_por_instancia['sintys']['match']} coincidencias SINTYS",
                tone="warning",
            ),
        ]

        paginator = Paginator(queryset.order_by("-creado_en"), PAGE_SIZE)
        page_obj = paginator.get_page(self.request.GET.get("page"))
        current_query = _clean_query_params(self.request.GET)
        current_query.pop("page", None)

        provincias = Provincia.objects.all().order_by("nombre")
        provincia_actual = None
        if provincia_id:
            provincia_actual = next(
                (provincia for provincia in provincias if str(provincia.id) == provincia_id),
                None,
            )

        filtros_activos = []
        if provincia_actual:
            filtros_activos.append({"label": "Provincia", "value": provincia_actual.nombre})
        if fecha_desde:
            filtros_activos.append({"label": "Desde", "value": fecha_desde})
        if fecha_hasta:
            filtros_activos.append({"label": "Hasta", "value": fecha_hasta})
        if revision_tecnico:
            filtros_activos.append(
                {
                    "label": "Validación",
                    "value": _find_definition_label(revision_tecnico, VALIDACION_ITEMS),
                }
            )
        if resultado_sintys:
            filtros_activos.append(
                {
                    "label": "SINTYS",
                    "value": _find_definition_label(resultado_sintys, SINTYS_ITEMS),
                }
            )
        if estado_cupo:
            filtros_activos.append(
                {
                    "label": "Cupo",
                    "value": _find_definition_label(estado_cupo, CUPO_ITEMS),
                }
            )
        if expediente_numero:
            filtros_activos.append({"label": "Expediente", "value": expediente_numero})
        if documento_persona:
            filtros_activos.append({"label": "Documento", "value": documento_persona})

        context.update(
            {
                "total_casos": total_casos,
                "casos_documentos_ok": casos_documentos_ok,
                "casos_documentos_incompletos": casos_documentos_incompletos,
                "porcentaje_documentos_ok": porcentaje_documentos_ok,
                "porcentaje_documentos_incompletos": porcentaje_documentos_incompletos,
                "casos_con_comentarios": casos_con_comentarios,
                "metricas_principales": metricas_principales,
                "casos_por_instancia": casos_por_instancia,
                "stats_validacion": stats_validacion,
                "stats_sintys": stats_sintys,
                "stats_cupo": stats_cupo,
                "resumen_validacion": resumen_validacion,
                "resumen_sintys": resumen_sintys,
                "resumen_cupo": resumen_cupo,
                "expedientes_por_provincia": expedientes_por_provincia,
                "tendencia_mensual": tendencia_mensual,
                "ultimos_casos": page_obj.object_list,
                "page_obj": page_obj,
                "page_range": paginator.get_elided_page_range(page_obj.number),
                "current_querystring": current_query.urlencode(),
                "detalle_desde": page_obj.start_index() if total_casos else 0,
                "detalle_hasta": page_obj.end_index() if total_casos else 0,
                "page_size": PAGE_SIZE,
                "provincias": provincias,
                "provincia_actual": provincia_actual,
                "provincia_seleccionada": provincia_id or "",
                "fecha_desde": fecha_desde or "",
                "fecha_hasta": fecha_hasta or "",
                "expediente_numero": expediente_numero or "",
                "documento_persona": documento_persona or "",
                "revision_tecnico": revision_tecnico or "",
                "resultado_sintys": resultado_sintys or "",
                "estado_cupo": estado_cupo or "",
                "es_usuario_provincial": es_usuario_provincial,
                "filtros_activos": filtros_activos,
            }
        )

        return context
