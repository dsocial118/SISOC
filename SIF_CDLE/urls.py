from django.urls import path
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from .views import *

urlpatterns = [
    # Derivaciones
    path('CDLE/derivaciones/listar', login_required(CDLEDerivacionesListView.as_view()), name='CDLE_derivaciones_listar'),
    path('CDLE/derivaciones/buscar', login_required(CDLEDerivacionesBuscarListView.as_view()), name='CDLE_derivaciones_buscar'),
    path('CDLE/derivaciones/ver/<pk>', login_required(CDLEDerivacionesDetailView.as_view()), name='CDLE_derivaciones_ver'),
    path('CDLE/derivaciones/editar/<pk>', login_required(CDLEDerivacionesUpdateView.as_view()), name='CDLE_derivaciones_editar'),
    path('CDLE/derivaciones/rechazo/<pk>', login_required(CDLEDerivacionesRechazo.as_view()), name='CDLE_derivaciones_rechazo'),
    # PreAdmisiones
    path('CDLE/preadmisiones/crear/<pk>', login_required(CDLEPreAdmisionesCreateView.as_view()), name='CDLE_preadmisiones_crear'),
    path('CDLE/preadmisiones/editar/<pk>', login_required(CDLEPreAdmisionesUpdateView.as_view()), name='CDLE_preadmisiones_editar'),
    path('CDLE/preadmisiones/ver/<pk>', login_required(CDLEPreAdmisionesDetailView.as_view()), name='CDLE_preadmisiones_ver'),
    path('CDLE/preadmisiones/ver2/<pk>', login_required(CDLEPreAdmisiones2DetailView.as_view()), name='CDLE_preadmisiones_ver2'),
    path('CDLE/preadmisiones/ver3/<pk>', login_required(CDLEPreAdmisiones3DetailView.as_view()), name='CDLE_preadmisiones_ver3'),
    path('CDLE/preadmisiones/listar', login_required(CDLEPreAdmisionesListView.as_view()), name='CDLE_preadmisiones_listar'),
    path('CDLE/preadmisiones/buscar', login_required(CDLEPreAdmisionesBuscarListView.as_view()), name='CDLE_preadmisiones_buscar'),
    path('CDLE/preadmisiones/eliminar/<pk>', login_required(CDLEPreAdmisionesDeleteView.as_view()), name='CDLE_preadmisiones_eliminar'),
    # Indice Ingreso
    path('CDLE/criterios_ingreso/crear', login_required(CDLECriteriosIngresoCreateView.as_view()), name='CDLE_criterios_ingreso_crear'),
    path('CDLE/indice_ingreso/crear/<pk>', login_required(CDLEIndiceIngresoCreateView.as_view()), name='CDLE_indiceingreso_crear'),
    #path('CDLE/indice_ivi_egreso/crear/<pk>', login_required(CDLEIndiceIviEgresoCreateView.as_view()), name='CDLE_indiceiviegreso_crear'),
    path('CDLE/indice_ingreso/ver/<pk>', login_required(CDLEIndiceIngresoDetailView.as_view()), name='CDLE_indiceingreso_ver'),
    path('CDLE/indice_ingreso/editar/<pk>', login_required(CDLEIndiceIngresoUpdateView.as_view()), name='CDLE_indiceingreso_editar'),
    # IVI
    path('CDLE/criterios_ivi/crear', login_required(CDLECriteriosIVICreateView.as_view()), name='CDLE_criterios_ivi_crear'),
    path('CDLE/indice_ivi/crear/<pk>', login_required(CDLEIndiceIviCreateView.as_view()), name='CDLE_indiceivi_crear'),
    path('CDLE/indice_ivi_egreso/crear/<pk>', login_required(CDLEIndiceIviEgresoCreateView.as_view()), name='CDLE_indiceiviegreso_crear'),
    path('CDLE/indice_ivi/ver/<pk>', login_required(CDLEIndiceIviDetailView.as_view()), name='CDLE_indiceivi_ver'),
    path('CDLE/indice_ivi/editar/<pk>', login_required(CDLEIndiceIviUpdateView.as_view()), name='CDLE_indiceivi_editar'),
    # Admisiones
    path('CDLE/admisiones/ver/<pk>', login_required(CDLEAdmisionesDetailView.as_view()), name='CDLE_admisiones_ver'),
    path('CDLE/admisiones/listar/', login_required(CDLEAdmisionesListView.as_view()), name='CDLE_admisiones_listar'),
    path('CDLE/admisiones/buscar', login_required(CDLEAdmisionesBuscarListView.as_view()), name='CDLE_admisiones_buscar'),
    path('CDLE/asignado_admisiones/ver/<pk>', login_required(CDLEAsignadoAdmisionDetail.as_view()), name='CDLE_asignado_admisiones_ver'),
    path('CDLE/inactiva_admisiones/ver/<pk>', login_required(CDLEInactivaAdmisionDetail.as_view()), name='CDLE_inactiva_admisiones_ver'),
    # Intervensiones
    path('CDLE/intervenciones/crear/<pk>', login_required(CDLEIntervencionesCreateView.as_view()), name='CDLE_intervenciones_crear'),
    path('CDLE/intervenciones/ver/<pk>', login_required(CDLEIntervencionesLegajosListView.as_view()), name='CDLE_intervenciones_legajos_listar'),
    path('CDLE/intervenciones/listar/', login_required(CDLEIntervencionesListView.as_view()), name='CDLE_intervenciones_listar'),
    path('CDLE/intervencion/ver/<pk>', login_required(CDLEIntervencionesDetail.as_view()), name='CDLE_intervencion_ver'),
    path('CDLE/intervenciones/editar/<pk>', login_required(CDLEIntervencionesUpdateView.as_view()), name='CDLE_intervencion_editar'),
    path('CDLE/intervenciones/borrar/<pk>', login_required(CDLEIntervencionesDeleteView.as_view()), name='CDLE_intervencion_borrar'),

    ]

