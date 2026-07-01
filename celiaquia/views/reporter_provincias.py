from collections import Counter
from datetime import datetime, time, timedelta
from urllib.parse import urlencode

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db.models import Count
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.views.generic import TemplateView

from ciudadanos.models import GrupoFamiliar  # pylint: disable=import-error
from celiaquia.models import (  # pylint: disable=import-error
    EstadoCupo,
    ExpedienteCiudadano,
    ResultadoSintys,
    RevisionTecnico,
)
from core.models import Provincia  # pylint: disable=import-error
from users.territorial_scope import (  # pylint: disable=import-error
    apply_territorial_scope,
    get_effective_scopes,
    get_full_province_scope_ids,
    is_territorial_user,
)


PAGE_SIZE = 12

VALIDACION_ITEMS = [
    {"code": RevisionTecnico.PENDIENTE, "label": "Pendiente", "tone": "neutral"},
    {"code": RevisionTecnico.APROBADO, "label": "Aprobado", "tone": "success"},
    {"code": RevisionTecnico.RECHAZADO, "label": "Rechazado", "tone": "danger"},
    {"code": RevisionTecnico.SUBSANAR, "label": "Subsanar", "tone": "warning"},
    {"code": RevisionTecnico.SUBSANADO, "label": "Subsanado", "tone": "accent"},
]

SINTYS_ITEMS = [
    {"code": ResultadoSintys.SIN_CRUCE, "label": "Sin cruce", "tone": "neutral"},
    {"code": ResultadoSintys.MATCH, "label": "Match", "tone": "success"},
    {"code": ResultadoSintys.NO_MATCH, "label": "No match", "tone": "danger"},
]

CUPO_ITEMS = [
    {"code": EstadoCupo.NO_EVAL, "label": "No evaluado", "tone": "neutral"},
    {"code": EstadoCupo.DENTRO, "label": "Dentro", "tone": "success"},
    {"code": EstadoCupo.FUERA, "label": "Fuera", "tone": "danger"},
]

# Clasificación de legajos APROBADOS por tipo de rol/edad. Las categorías son
# mutuamente excluyentes (un legajo cae en una sola) con esta precedencia:
# menor de edad -> doble rol -> responsable -> beneficiario. Así los subtotales
# suman el total de aprobados.
CLASIFICACION_APROBADOS_ITEMS = [
    {"code": "beneficiario", "label": "Beneficiario únicamente", "tone": "success"},
    {
        "code": "doble_rol",
        "label": "Beneficiario y responsable (doble rol)",
        "tone": "accent",
    },
    {"code": "responsable", "label": "Responsable únicamente", "tone": "primary"},
    {"code": "menor", "label": "Menor de edad", "tone": "warning"},
]

VALIDACION_LABELS = {item["code"]: item["label"] for item in VALIDACION_ITEMS}
SINTYS_LABELS = {item["code"]: item["label"] for item in SINTYS_ITEMS}
CUPO_LABELS = {item["code"]: item["label"] for item in CUPO_ITEMS}

QUERY_PARAM_LABELS = {
    "fecha_desde": "Desde",
    "fecha_hasta": "Hasta",
    "expediente_numero": "Expediente",
    "documento_persona": "Documento",
    "revision_tecnico": "Validacion tecnica",
    "resultado_sintys": "Cruce SINTYS",
    "estado_cupo": "Estado de cupo",
}


def _percentage(count, total):
    if not total:
        return 0.0

    return round((count / total) * 100, 1)


def _format_percentage(value):
    return f"{value:.1f}%".replace(".", ",")


def _group_counts(queryset, field_name):
    grouped = queryset.values(field_name).annotate(count=Count("id"))
    return {row[field_name]: row["count"] for row in grouped}


def _build_status_items(stats, items, total_cases):
    max_count = max((stats.get(item["code"], 0) for item in items), default=0)
    summary = []

    for item in items:
        count = stats.get(item["code"], 0)
        size = round((count / max_count) * 100, 1) if max_count else 0.0
        summary.append(
            {
                **item,
                "count": count,
                "percentage": _percentage(count, total_cases),
                "size": size,
            }
        )

    return summary


def _build_metricas_principales(
    total_cases, ok_cases, incomplete_cases, comments_count
):
    return [
        {
            "label": "Casos totales",
            "value": str(total_cases),
            "support": "Casos filtrados en la lectura actual",
            "tone": "primary",
        },
        {
            "label": "Documentacion incompleta",
            "value": _format_percentage(_percentage(incomplete_cases, total_cases)),
            "support": f"{incomplete_cases} legajos con archivos pendientes",
            "tone": "warning",
        },
        {
            "label": "Documentacion completa",
            "value": _format_percentage(_percentage(ok_cases, total_cases)),
            "support": f"{ok_cases} legajos con archivos completos",
            "tone": "success",
        },
        {
            "label": "Casos con comentarios",
            "value": str(comments_count),
            "support": "Registros con seguimiento agregado",
            "tone": "accent",
        },
    ]


def _build_tendencia_mensual(queryset):
    # El agrupado mensual se hace en Python en lugar de delegar en TruncMonth.
    # En MySQL, Trunc*/Extract* sobre DateTimeField con USE_TZ=True emiten
    # CONVERT_TZ(..., 'UTC', settings.TIME_ZONE), que devuelve NULL si la base no
    # tiene cargadas/activas las tablas mysql.time_zone* (el caso de produccion).
    # Ver docs/registro/decisiones/2026-06-04-tendencia-mensual-sin-convert-tz.md.
    cutoff = timezone.now() - timedelta(days=180)
    fechas = queryset.filter(creado_en__gte=cutoff).values_list("creado_en", flat=True)

    buckets = Counter()
    for creado_en in fechas:
        if creado_en is None:
            continue
        local = (
            timezone.localtime(creado_en) if timezone.is_aware(creado_en) else creado_en
        )
        buckets[(local.year, local.month)] += 1

    if not buckets:
        return []

    max_count = max(buckets.values())
    return [
        {
            "label": f"{month:02d}/{year}",
            "count": count,
            "size": round((count / max_count) * 100, 1) if max_count else 0.0,
        }
        for (year, month), count in sorted(buckets.items())
    ]


def _build_expedientes_por_provincia(queryset, total_cases):
    # Se agrupa directamente sobre el queryset de legajos (mismo universo que
    # total_casos) en lugar de re-derivar desde Expediente.objects. Así la suma
    # de "casos" coincide con total_casos y los "share" suman 100%, y no se
    # pierden legajos vivos cuyo expediente padre esté soft-deleted.
    rows = list(
        queryset.values(
            "ciudadano__provincia_id",
            "ciudadano__provincia__nombre",
        )
        .annotate(
            casos=Count("id", distinct=True),
            expedientes=Count("expediente_id", distinct=True),
        )
        .order_by("-casos", "ciudadano__provincia__nombre")
    )

    max_cases = max((row["casos"] for row in rows), default=0)
    provincias = []

    for row in rows:
        casos = row["casos"]
        provincias.append(
            {
                "provincia_id": row["ciudadano__provincia_id"],
                "nombre": row["ciudadano__provincia__nombre"] or "Sin provincia",
                "expedientes": row["expedientes"],
                "casos": casos,
                "share": _percentage(casos, total_cases),
                "size": round((casos / max_cases) * 100, 1) if max_cases else 0.0,
            }
        )

    return provincias


def _build_current_querystring(request):
    params = {
        key: value
        for key, value in request.GET.items()
        if key != "page" and str(value).strip()
    }
    return urlencode(params)


def _build_filtros_activos(request, provincia_actual):
    filtros = []

    provincia_id = request.GET.get("provincia")
    if provincia_id:
        filtros.append(
            {
                "label": "Provincia",
                "value": provincia_actual.nombre if provincia_actual else provincia_id,
            }
        )

    for field_name, label in QUERY_PARAM_LABELS.items():
        value = request.GET.get(field_name)
        if not value:
            continue

        if field_name == "revision_tecnico":
            value = VALIDACION_LABELS.get(value, value)
        elif field_name == "resultado_sintys":
            value = SINTYS_LABELS.get(value, value)
        elif field_name == "estado_cupo":
            value = CUPO_LABELS.get(value, value)

        filtros.append({"label": label, "value": value})

    return filtros


def _get_provincia_actual(request, es_usuario_provincial):
    provincia_id = request.GET.get("provincia")

    # Un usuario provincial no puede fijar como "alcance" una provincia fuera de
    # su scope: si el ?provincia= no pertenece a sus scopes, se ignora (evita que
    # el chip "Alcance"/"Provincia" muestre el nombre de una provincia ajena).
    if provincia_id and es_usuario_provincial:
        provincia_ids = {
            scope.provincia_id for scope in get_effective_scopes(request.user)
        }
        try:
            solicitada = int(provincia_id)
        except (TypeError, ValueError):
            solicitada = None
        if solicitada not in provincia_ids:
            provincia_id = None

    if provincia_id:
        return Provincia.objects.filter(pk=provincia_id).first()

    if not es_usuario_provincial:
        return None

    provincia_ids = [scope.provincia_id for scope in get_effective_scopes(request.user)]
    return Provincia.objects.filter(pk__in=provincia_ids).order_by("nombre").first()


def _get_provincias_disponibles(user, es_usuario_provincial):
    if es_usuario_provincial:
        # Solo provincias con alcance completo: ofrecer una provincia entera a
        # quien únicamente tiene scope municipal sería incoherente con los datos.
        provincia_ids = get_full_province_scope_ids(user)
        return Provincia.objects.filter(pk__in=provincia_ids).order_by("nombre")

    return Provincia.objects.all().order_by("nombre")


def _build_pagination(queryset, request):
    # "-pk" como desempate estable: sin él, los muchos legajos con igual creado_en
    # (importaciones masivas en el mismo instante) se ordenan de forma no
    # determinista entre páginas y el listado repite/saltea filas.
    paginator = Paginator(queryset.order_by("-creado_en", "-pk"), PAGE_SIZE)
    page_obj = paginator.get_page(request.GET.get("page"))
    current_querystring = _build_current_querystring(request)
    return paginator, page_obj, current_querystring


def _extract_filter_values(request):
    return {
        "provincia": request.GET.get("provincia"),
        "fecha_desde": request.GET.get("fecha_desde"),
        "fecha_hasta": request.GET.get("fecha_hasta"),
        "expediente_numero": request.GET.get("expediente_numero"),
        "documento_persona": request.GET.get("documento_persona"),
        "revision_tecnico": request.GET.get("revision_tecnico"),
        "resultado_sintys": request.GET.get("resultado_sintys"),
        "estado_cupo": request.GET.get("estado_cupo"),
    }


def _apply_report_filters(queryset, filter_values):
    if filter_values["provincia"]:
        queryset = queryset.filter(ciudadano__provincia_id=filter_values["provincia"])
    # Los <input type=date> entregan 'YYYY-MM-DD' sin hora. Construimos límites
    # aware para incluir el día completo: desde 00:00 del día "desde" hasta el
    # instante previo a 00:00 del día siguiente al "hasta" (rango inclusivo).
    # Evita el sesgo de creado_en__lte='YYYY-MM-DD' (que cortaba en medianoche
    # local y excluía todo el último día) y el RuntimeWarning por naive datetime.
    fecha_desde = parse_date(filter_values["fecha_desde"] or "")
    if fecha_desde:
        inicio = timezone.make_aware(datetime.combine(fecha_desde, time.min))
        queryset = queryset.filter(creado_en__gte=inicio)
    fecha_hasta = parse_date(filter_values["fecha_hasta"] or "")
    if fecha_hasta:
        fin = timezone.make_aware(
            datetime.combine(fecha_hasta + timedelta(days=1), time.min)
        )
        queryset = queryset.filter(creado_en__lt=fin)
    if filter_values["expediente_numero"]:
        queryset = queryset.filter(
            expediente__numero_expediente__icontains=filter_values["expediente_numero"]
        )
    if filter_values["documento_persona"]:
        queryset = queryset.filter(
            ciudadano__documento__icontains=filter_values["documento_persona"]
        )
    if filter_values["revision_tecnico"]:
        queryset = queryset.filter(revision_tecnico=filter_values["revision_tecnico"])
    if filter_values["resultado_sintys"]:
        queryset = queryset.filter(resultado_sintys=filter_values["resultado_sintys"])
    if filter_values["estado_cupo"]:
        queryset = queryset.filter(estado_cupo=filter_values["estado_cupo"])

    return queryset


def _es_menor(fecha_nacimiento, hoy):
    if not fecha_nacimiento:
        return False
    edad = (
        hoy.year
        - fecha_nacimiento.year
        - ((hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day))
    )
    return edad < 18


def _clasificar_legajo_aprobado(
    rol, fecha_nacimiento, hoy, es_beneficiario_familia=False
):
    if _es_menor(fecha_nacimiento, hoy):
        return "menor"
    rol = (rol or "").strip().lower()
    if rol == ExpedienteCiudadano.ROLE_BENEFICIARIO_Y_RESPONSABLE:
        return "doble_rol"
    if rol == ExpedienteCiudadano.ROLE_RESPONSABLE:
        # Un responsable que además es beneficiario en su grupo familiar (figura
        # como hijo de otro cuidador principal) es doble rol, igual que en el
        # detalle del expediente. Sin ese vínculo, es responsable únicamente.
        return "doble_rol" if es_beneficiario_familia else "responsable"
    return "beneficiario"


def _build_clasificacion_aprobados(queryset):
    """Clasifica los legajos APROBADOS por tipo de rol/edad (categorías mutuamente
    excluyentes). Devuelve el total de aprobados y los subtotales por categoría."""
    hoy = timezone.localdate()
    filas = list(
        queryset.filter(revision_tecnico=RevisionTecnico.APROBADO).values_list(
            "ciudadano_id", "rol", "ciudadano__fecha_nacimiento"
        )
    )
    ciudadano_ids = [ciudadano_id for ciudadano_id, _, _ in filas]
    # Ciudadanos aprobados que son beneficiarios dentro de una relación familiar
    # (figuran como hijo con cuidador principal). Una sola consulta batch.
    beneficiarios_familia = set(
        GrupoFamiliar.objects.filter(
            ciudadano_2_id__in=ciudadano_ids,
            cuidador_principal=True,
        ).values_list("ciudadano_2_id", flat=True)
    )

    counts = Counter(
        _clasificar_legajo_aprobado(
            rol, fecha_nacimiento, hoy, ciudadano_id in beneficiarios_familia
        )
        for ciudadano_id, rol, fecha_nacimiento in filas
    )
    total = sum(counts.values())
    max_count = max(counts.values(), default=0)

    items = [
        {
            **item,
            "count": counts.get(item["code"], 0),
            "percentage": _percentage(counts.get(item["code"], 0), total),
            "size": (
                round((counts.get(item["code"], 0) / max_count) * 100, 1)
                if max_count
                else 0.0
            ),
        }
        for item in CLASIFICACION_APROBADOS_ITEMS
    ]

    return {"total": total, "items": items}


def _build_case_context(queryset, total_cases, excluir_comentarios_internos=False):
    ok_cases = queryset.filter(archivos_ok=True).count()
    incomplete_cases = total_cases - ok_cases
    # Los comentarios internos no deben contarse para usuarios provinciales: un
    # legajo con solo comentarios internos no figura como "con comentarios".
    comments_count = (
        queryset.filter(
            **(
                {"historial_comentarios__es_interno": False}
                if excluir_comentarios_internos
                else {"historial_comentarios__isnull": False}
            )
        )
        .values("id")
        .distinct()
        .count()
    )

    stats_validacion = _group_counts(queryset, "revision_tecnico")
    stats_sintys = _group_counts(queryset, "resultado_sintys")
    stats_cupo = _group_counts(queryset, "estado_cupo")

    resumen_validacion = _build_status_items(
        stats_validacion,
        VALIDACION_ITEMS,
        total_cases,
    )
    resumen_sintys = _build_status_items(stats_sintys, SINTYS_ITEMS, total_cases)
    resumen_cupo = _build_status_items(stats_cupo, CUPO_ITEMS, total_cases)

    validacion_lookup = {item["code"]: item["count"] for item in resumen_validacion}
    sintys_lookup = {item["code"]: item["count"] for item in resumen_sintys}
    cupo_lookup = {item["code"]: item["count"] for item in resumen_cupo}

    return {
        "casos_documentos_ok": ok_cases,
        "casos_documentos_incompletos": incomplete_cases,
        "porcentaje_documentos_ok": _percentage(ok_cases, total_cases),
        "porcentaje_documentos_incompletos": _percentage(incomplete_cases, total_cases),
        "casos_con_comentarios": comments_count,
        "metricas_principales": _build_metricas_principales(
            total_cases,
            ok_cases,
            incomplete_cases,
            comments_count,
        ),
        "casos_por_instancia": {
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
        },
        "stats_validacion": stats_validacion,
        "stats_sintys": stats_sintys,
        "stats_cupo": stats_cupo,
        "resumen_validacion": resumen_validacion,
        "resumen_sintys": resumen_sintys,
        "resumen_cupo": resumen_cupo,
        "clasificacion_aprobados": _build_clasificacion_aprobados(queryset),
        "tendencia_mensual": _build_tendencia_mensual(queryset),
        "expedientes_por_provincia": _build_expedientes_por_provincia(
            queryset,
            total_cases,
        ),
    }


def _build_report_context(request):
    user = request.user
    es_usuario_provincial = is_territorial_user(user)

    queryset = ExpedienteCiudadano.objects.select_related(
        "expediente__usuario_provincia__profile",
        "ciudadano",
        "ciudadano__provincia",
        "estado",
    )

    if es_usuario_provincial:
        queryset = apply_territorial_scope(
            queryset,
            user,
            provincia_lookup="ciudadano__provincia_id",
            municipio_lookup="ciudadano__municipio_id",
            localidad_lookup="ciudadano__localidad_id",
        )

    filter_values = _extract_filter_values(request)
    queryset = _apply_report_filters(queryset, filter_values)

    provincia_actual = _get_provincia_actual(request, es_usuario_provincial)
    total_casos = queryset.count()
    report_context = _build_case_context(
        queryset,
        total_casos,
        excluir_comentarios_internos=es_usuario_provincial,
    )
    provincias = _get_provincias_disponibles(user, es_usuario_provincial)
    paginator, page_obj, current_querystring = _build_pagination(queryset, request)

    return {
        "total_casos": total_casos,
        **report_context,
        "ultimos_casos": page_obj.object_list,
        "page_obj": page_obj,
        "page_range": paginator.get_elided_page_range(page_obj.number),
        "current_querystring": current_querystring,
        "detalle_desde": page_obj.start_index() if total_casos else 0,
        "detalle_hasta": page_obj.end_index() if total_casos else 0,
        "page_size": PAGE_SIZE,
        "provincias": provincias,
        "provincia_actual": provincia_actual,
        "provincia_seleccionada": filter_values["provincia"] or "",
        "fecha_desde": filter_values["fecha_desde"] or "",
        "fecha_hasta": filter_values["fecha_hasta"] or "",
        "expediente_numero": filter_values["expediente_numero"] or "",
        "documento_persona": filter_values["documento_persona"] or "",
        "revision_tecnico": filter_values["revision_tecnico"] or "",
        "resultado_sintys": filter_values["resultado_sintys"] or "",
        "estado_cupo": filter_values["estado_cupo"] or "",
        "es_usuario_provincial": es_usuario_provincial,
        "filtros_activos": _build_filtros_activos(request, provincia_actual),
    }


class ReporterProvinciasView(LoginRequiredMixin, TemplateView):
    template_name = "celiaquia/reporter_provincias.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(_build_report_context(self.request))

        return context
