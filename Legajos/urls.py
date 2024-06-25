from django.urls import path
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from .views import *

urlpatterns = [
    # Legajos
    path('legajos/reportes', login_required(LegajosReportesListView.as_view()), name='legajos_reportes'),
    path('legajos/listar', login_required(LegajosListView.as_view()), name='legajos_listar'),
    path('legajos/listar/<busqueda>', login_required(LegajosListView.as_view()), name='legajos_listar'),
    # path('legajos/busqueda', login_required(busquedaLegajos.as_view()),name='legajos_listar'),
    path('legajos/crear/', login_required(LegajosCreateView.as_view()), name='legajos_crear'),
    path('legajos/ver/<pk>', login_required(LegajosDetailView.as_view()), name='legajos_ver'),
    path('legajos/editar/<pk>', login_required(LegajosUpdateView.as_view()), name='legajos_editar'),
    path('legajos/eliminar/<pk>', login_required(LegajosDeleteView.as_view()), name='legajos_eliminar'),
    # Legajos Grupo Familiar
    path('legajos/grupofamiliar/listar/<pk>', login_required(LegajoGrupoFamiliarList.as_view()), name='grupofamiliar_listar'),
    path('legajos/grupofamiliar/crear/<pk>', login_required(LegajosGrupoFamiliarCreateView.as_view()), name='grupofamiliar_crear'),
    path('legajos/grupofamiliar/crear/ajax/', login_required(CreateGrupoFamiliar.as_view()), name='grupofamiliar_ajax_crear'),
    path('legajos/grupofamiliar/borrar/ajax/', login_required(DeleteGrupoFamiliar.as_view()), name='grupofamiliar_ajax_borrar'),
    path('legajos/grupofamiliar/buscar/', login_required(busqueda_familiares), name='familiares_buscar'),
    path('legajos/grupofamiliar/nuevo/', login_required(LegajosGrupoFamiliarCreateView.as_view()), name='nuevoLegajoFamiliar_ajax'),
    # Dimensiones
    path('legajos/dimensiones/ver/<pk>', login_required(DimensionesDetailView.as_view()), name='legajosdimensiones_ver'),
    path('legajos/dimensiones/editar/<pk>', login_required(DimensionesUpdateView.as_view()), name='legajosdimensiones_editar'),
    # Legajos Alertas
    path('legajos/alertas/listar/<pk>', login_required(LegajosAlertasListView.as_view()), name='legajoalertas_listar'),
    path('legajos/alertas/crear/<pk>', login_required(LegajosAlertasCreateView.as_view()), name='legajoalertas_crear'),
    path('legajos/alertas/borrar/ajax/', login_required(DeleteAlerta.as_view()), name='alerta_ajax_borrar'),
    # path('legajos/alertas/crear/ajax/', login_required(CreateAlerta.as_view()), name='alerta_ajax_crear'),    
    # URLs para los select dinamicos para legajoalertas_form
    path('alertas-select/', AlertasSelectView.as_view(), name='alertas_select'),
    path('categorias-select/', CategoriasSelectView.as_view(), name='categorias_select'),
    # Legajos Archivos
    path('legajos/archivos/listar/<pk>', login_required(LegajosArchivosListView.as_view()), name='legajosarchivos_listar'),
    path('legajos/archivos/crear/<pk>', login_required(LegajosArchivosCreateView.as_view()), name='legajosarchivos_crear'),
    path('legajos/archivos/crear/ajax/', login_required(CreateArchivo.as_view()), name='archivo_ajax_crear'),    
    path('legajos/archivos/borrar/ajax/', login_required(DeleteArchivo.as_view()), name='archivo_ajax_borrar'),
    # Derivaciones
    path('legajos/derivaciones/buscar', login_required(LegajosDerivacionesBuscar.as_view()), name='legajosderivaciones_buscar'),
    path('legajos/derivaciones/derivar/<pk>', login_required(LegajosDerivacionesCreateView.as_view()), name='legajosderivaciones_crear'),
    path('legajos/derivaciones/listar', login_required(LegajosDerivacionesListView.as_view()), name='legajosderivaciones_listar'),
    path('legajos/derivaciones/listar/<str:filtro>', login_required(LegajosDerivacionesListView.as_view()), name='legajosderivaciones_listar'),
    path('legajos/derivaciones/ver/<pk>', login_required(LegajosDerivacionesDetailView.as_view()), name='legajosderivaciones_ver'),
    path('legajos/derivaciones/editar/<pk>', login_required(LegajosDerivacionesUpdateView.as_view()), name='legajosderivaciones_editar'),
    path('legajos/derivaciones/eliminar/<pk>', login_required(LegajosDerivacionesDeleteView.as_view()), name='legajosderivaciones_eliminar'),
    path('legajos/derivaciones/historial/<pk>', login_required(LegajosDerivacionesHistorial.as_view()), name='legajosderivaciones_historial'),
     # Plantilla Programas de asistencia
    path('legajos/programas_intervencion/<pk>', login_required(programasIntervencionesView.as_view()), name='programas_intervencion'),
     # Plantilla Acciones Sociales
    path('legajos/acciones_sociales/<pk>', login_required(accionesSocialesView.as_view()), name='acciones_sociales'),
     # Plantilla Interveciones de salud
    path('legajos/intervenciones_salud/<pk>', login_required(intervencionesSaludView.as_view()), name='intervenciones_salud'),
     # Plantilla Indices
    path('legajos/indices/<pk>', login_required(indicesView.as_view()), name='indices'),
    # Plantilla Indice detalle
    path('legajos/indices_detalle/<pk>', login_required(indicesDetalleView.as_view()), name='indices_detalle'),
    # Legajos Hogar
    path('legajos/grupoHogar/listar/<pk>', login_required(LegajoGrupoHogarList.as_view()), name='grupohogar_listar'),
    path('legajos/grupoHogar/crear/<pk>', login_required(LegajosGrupoHogarCreateView.as_view()), name='grupohogar_crear'),
    path('legajos/grupoHogar/crear/ajax/', login_required(CreateGrupoHogar.as_view()), name='grupohogar_ajax_crear'),
    path('legajos/grupoHogar/borrar/ajax/', login_required(DeleteGrupoHogar.as_view()), name='grupohogar_ajax_borrar'),
    path('legajos/grupoHogar/buscar/', login_required(busqueda_hogar), name='hogar_buscar'),
    path('legajos/grupoHogar/nuevo/', login_required(LegajosGrupoHogarCreateView.as_view()), name='nuevoLegajoFamiliar_ajax'),
    path('legajos/hogar/crear/<pk>', login_required(LegajosGrupoHogarCreateView.as_view()), name='legajosgrupohogar_crear'),

]
