from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q, F, Case, When, IntegerField
from django.utils import timezone
from datetime import timedelta
from core.models import Provincia
from celiaquia.models import ExpedienteCiudadano, Expediente


class ReporterProvinciasView(LoginRequiredMixin, TemplateView):
    template_name = "celiaquia/reporter_provincias.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Detectar si es usuario provincial
        es_usuario_provincial = False
        provincia_usuario = None
        try:
            if hasattr(user, 'profile') and user.profile.es_usuario_provincial:
                es_usuario_provincial = True
                provincia_usuario = user.profile.provincia
        except Exception:
            pass

        # Obtener parámetros de filtro
        provincia_id = self.request.GET.get("provincia")
        
        # Si es usuario provincial, forzar su provincia
        if es_usuario_provincial and provincia_usuario:
            provincia_id = str(provincia_usuario.id)
        
        fecha_desde = self.request.GET.get("fecha_desde")
        fecha_hasta = self.request.GET.get("fecha_hasta")
        expediente_numero = self.request.GET.get("expediente_numero")
        documento_persona = self.request.GET.get("documento_persona")
        revision_tecnico = self.request.GET.get("revision_tecnico")
        resultado_sintys = self.request.GET.get("resultado_sintys")
        estado_cupo = self.request.GET.get("estado_cupo")

        # Filtro base
        queryset = ExpedienteCiudadano.objects.select_related(
            "expediente__usuario_provincia__profile", "ciudadano", "estado"
        )

        # Aplicar filtros
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

        # Estadísticas generales
        total_casos = queryset.count()

        # Estados de validación técnica
        stats_validacion = (
            queryset.values("revision_tecnico")
            .annotate(count=Count("id"))
            .order_by("revision_tecnico")
        )

        # Resultados SINTYS
        stats_sintys = (
            queryset.values("resultado_sintys")
            .annotate(count=Count("id"))
            .order_by("resultado_sintys")
        )

        # Estados de cupo
        stats_cupo = (
            queryset.values("estado_cupo")
            .annotate(count=Count("id"))
            .order_by("estado_cupo")
        )

        # Casos por instancia
        casos_por_instancia = {
            "validacion_tecnica": {
                "pendiente": queryset.filter(revision_tecnico="PENDIENTE").count(),
                "aprobado": queryset.filter(revision_tecnico="APROBADO").count(),
                "rechazado": queryset.filter(revision_tecnico="RECHAZADO").count(),
                "subsanar": queryset.filter(revision_tecnico="SUBSANAR").count(),
                "subsanado": queryset.filter(revision_tecnico="SUBSANADO").count(),
            },
            "sintys": {
                "sin_cruce": queryset.filter(resultado_sintys="SIN_CRUCE").count(),
                "match": queryset.filter(resultado_sintys="MATCH").count(),
                "no_match": queryset.filter(resultado_sintys="NO_MATCH").count(),
            },
            "cupo": {
                "no_eval": queryset.filter(estado_cupo="NO_EVAL").count(),
                "dentro": queryset.filter(estado_cupo="DENTRO").count(),
                "fuera": queryset.filter(estado_cupo="FUERA").count(),
            },
        }

        # Casos con documentos completos
        casos_documentos_ok = queryset.filter(archivos_ok=True).count()
        casos_documentos_incompletos = total_casos - casos_documentos_ok
        porcentaje_documentos_ok = (
            round((casos_documentos_ok / total_casos) * 100, 1) if total_casos else 0
        )
        porcentaje_documentos_incompletos = (
            round((casos_documentos_incompletos / total_casos) * 100, 1)
            if total_casos
            else 0
        )

        # Casos con comentarios
        casos_con_comentarios = (
            queryset.filter(historial_comentarios__isnull=False).distinct().count()
        )

        # Expedientes por provincia
        expedientes_por_provincia = (
            Expediente.objects.filter(expediente_ciudadanos__in=queryset)
            .values("usuario_provincia__profile__provincia__nombre")
            .annotate(
                total=Count("id", distinct=True),
                casos=Count("expediente_ciudadanos", distinct=True),
            )
            .order_by("-casos")
        )

        # Últimos casos (para tabla de detalle)
        ultimos_casos = queryset.order_by("-creado_en")[:50]

        # Provincias disponibles
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
                "casos_por_instancia": casos_por_instancia,
                "stats_validacion": stats_validacion,
                "stats_sintys": stats_sintys,
                "stats_cupo": stats_cupo,
                "expedientes_por_provincia": expedientes_por_provincia,
                "ultimos_casos": ultimos_casos,
                "provincias": provincias,
                "provincia_seleccionada": provincia_id or "",
                "fecha_desde": fecha_desde or "",
                "fecha_hasta": fecha_hasta or "",
                "expediente_numero": expediente_numero or "",
                "documento_persona": documento_persona or "",
                "revision_tecnico": revision_tecnico or "",
                "resultado_sintys": resultado_sintys or "",
                "estado_cupo": estado_cupo or "",
                "es_usuario_provincial": es_usuario_provincial,
            }
        )

        return context
