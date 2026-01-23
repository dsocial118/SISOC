from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q, F, Case, When, IntegerField
from django.utils import timezone
from datetime import timedelta
from core.models import Provincia
from celiaquia.models import (
    ExpedienteCiudadano, 
    Expediente
)


class ReporterProvinciasView(LoginRequiredMixin, TemplateView):
    template_name = 'celiaquia/reporter_provincias.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obtener parámetros de filtro
        provincia_id = self.request.GET.get('provincia')
        fecha_desde = self.request.GET.get('fecha_desde')
        fecha_hasta = self.request.GET.get('fecha_hasta')
        estado_filtro = self.request.GET.get('estado')
        
        # Filtro base
        queryset = ExpedienteCiudadano.objects.select_related(
            'expediente__usuario_provincia__profile',
            'ciudadano',
            'estado'
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
        
        if estado_filtro:
            queryset = queryset.filter(estado__nombre=estado_filtro)
        
        # Estadísticas generales
        total_casos = queryset.count()
        
        # Estados de validación técnica
        stats_validacion = queryset.values('revision_tecnico').annotate(
            count=Count('id')
        ).order_by('revision_tecnico')
        
        # Resultados SINTYS
        stats_sintys = queryset.values('resultado_sintys').annotate(
            count=Count('id')
        ).order_by('resultado_sintys')
        
        # Estados de cupo
        stats_cupo = queryset.values('estado_cupo').annotate(
            count=Count('id')
        ).order_by('estado_cupo')
        
        # Casos por instancia
        casos_por_instancia = {
            'validacion_tecnica': {
                'pendiente': queryset.filter(revision_tecnico='PENDIENTE').count(),
                'aprobado': queryset.filter(revision_tecnico='APROBADO').count(),
                'rechazado': queryset.filter(revision_tecnico='RECHAZADO').count(),
                'subsanar': queryset.filter(revision_tecnico='SUBSANAR').count(),
                'subsanado': queryset.filter(revision_tecnico='SUBSANADO').count(),
            },
            'sintys': {
                'sin_cruce': queryset.filter(resultado_sintys='SIN_CRUCE').count(),
                'match': queryset.filter(resultado_sintys='MATCH').count(),
                'no_match': queryset.filter(resultado_sintys='NO_MATCH').count(),
            },
            'cupo': {
                'no_eval': queryset.filter(estado_cupo='NO_EVAL').count(),
                'dentro': queryset.filter(estado_cupo='DENTRO').count(),
                'fuera': queryset.filter(estado_cupo='FUERA').count(),
            }
        }
        
        # Casos con documentos completos
        casos_documentos_ok = queryset.filter(archivos_ok=True).count()
        casos_documentos_incompletos = total_casos - casos_documentos_ok
        
        # Casos con comentarios
        casos_con_comentarios = queryset.filter(
            historial_comentarios__isnull=False
        ).distinct().count()
        
        # Expedientes por provincia
        expedientes_por_provincia = Expediente.objects.filter(
            expediente_ciudadanos__in=queryset
        ).values(
            'usuario_provincia__profile__provincia__nombre'
        ).annotate(
            total=Count('id', distinct=True),
            casos=Count('expediente_ciudadanos', distinct=True)
        ).order_by('-casos')
        
        # Últimos casos (para tabla de detalle)
        ultimos_casos = queryset.order_by('-creado_en')[:50]
        
        # Provincias disponibles
        provincias = Provincia.objects.all().order_by('nombre')
        
        # Preparar datos para gráficos
        context.update({
            'total_casos': total_casos,
            'casos_documentos_ok': casos_documentos_ok,
            'casos_documentos_incompletos': casos_documentos_incompletos,
            'casos_con_comentarios': casos_con_comentarios,
            'casos_por_instancia': casos_por_instancia,
            'stats_validacion': stats_validacion,
            'stats_sintys': stats_sintys,
            'stats_cupo': stats_cupo,
            'expedientes_por_provincia': expedientes_por_provincia,
            'ultimos_casos': ultimos_casos,
            'provincias': provincias,
            'provincia_seleccionada': provincia_id,
            'fecha_desde': fecha_desde,
            'fecha_hasta': fecha_hasta,
            'estado_filtro': estado_filtro,
        })
        
        return context
