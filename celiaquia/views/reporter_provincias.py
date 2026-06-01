from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q, F, Case, When, IntegerField
from django.utils import timezone
from datetime import timedelta
from core.models import Provincia
from celiaquia.models import ExpedienteCiudadano, Expediente
from users.territorial_scope import (
    apply_territorial_scope,
    get_effective_scopes,
    is_territorial_user,
)


class ReporterProvinciasView(LoginRequiredMixin, TemplateView):
    template_name = "celiaquia/reporter_provincias.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        es_usuario_provincial = is_territorial_user(user)

        # Obtener parámetros de filtro
        provincia_id = self.request.GET.get("provincia")

        fecha_desde = self.request.GET.get("fecha_desde")
        fecha_hasta = self.request.GET.get("fecha_hasta")
        expediente_numero = self.request.GET.get("expediente_numero")
        documento_persona = self.request.GET.get("documento_persona")
        revision_tecnico = self.request.GET.get("revision_tecnico")
        resultado_sintys = self.request.GET.get("resultado_sintys")
        estado_cupo = self.request.GET.get("estado_cupo")

        queryset = ExpedienteCiudadano.objects.select_related(
            "expediente__usuario_provincia__profile", "ciudadano", "estado"
        )

        if es_usuario_provincial:
            queryset = apply_territorial_scope(
                queryset,
                user,
                provincia_lookup="ciudadano__provincia_id",
                municipio_lookup="ciudadano__municipio_id",
                localidad_lookup="ciudadano__localidad_id",
                own_lookup="expediente__usuario_provincia",
                include_own=True,
            )

        if provincia_id:
            queryset = queryset.filter(ciudadano__provincia_id=provincia_id)

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

        # Expedientes por provincia
        expedientes_por_provincia = (
            Expediente.objects.filter(expediente_ciudadanos__in=queryset)
            .values("expediente_ciudadanos__ciudadano__provincia__nombre")
            .annotate(
                total=Count("id", distinct=True),
                casos=Count("expediente_ciudadanos", distinct=True),
            )
            .order_by("-casos")
        )

        # Últimos casos (para tabla de detalle)
        ultimos_casos = queryset.order_by("-creado_en")[:50]

        # Provincias disponibles
        if es_usuario_provincial:
            provincia_ids = {scope.provincia_id for scope in get_effective_scopes(user)}
            provincias = Provincia.objects.filter(pk__in=provincia_ids).order_by(
                "nombre"
            )
        else:
            provincias = Provincia.objects.all().order_by("nombre")

        # Preparar datos para gráficos
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
