from django.urls import path
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from .views import *

urlpatterns = [
    # Derivaciones
    path('MA/derivaciones/listar', login_required(MADerivacionesListView.as_view()), name='MA_derivaciones_listar'),
    path('MA/derivaciones/buscar', login_required(MADerivacionesBuscarListView.as_view()), name='MA_derivaciones_buscar'),
    path('MA/derivaciones/ver/<pk>', login_required(MADerivacionesDetailView.as_view()), name='MA_derivaciones_ver'),
    path('MA/derivaciones/editar/<pk>', login_required(MADerivacionesUpdateView.as_view()), name='MA_derivaciones_editar'),
    path('MA/derivaciones/rechazo/<pk>', login_required(MADerivacionesRechazo.as_view()), name='MA_derivaciones_rechazo'),
    # PreAdmisiones
    path('MA/preadmisiones/crear/<pk>', login_required(MAPreAdmisionesCreateView.as_view()), name='MA_preadmisiones_crear'),
    path('MA/preadmisiones/editar/<pk>', login_required(MAPreAdmisionesUpdateView.as_view()), name='MA_preadmisiones_editar'),
    path('MA/preadmisiones/ver/<pk>', login_required(MAPreAdmisionesDetailView.as_view()), name='MA_preadmisiones_ver'),
    path('MA/preadmisiones/ver3/<pk>', login_required(MAPreAdmisiones3DetailView.as_view()), name='MA_preadmisiones_ver3'),
    path('MA/preadmisiones/listar', login_required(MAPreAdmisionesListView.as_view()), name='MA_preadmisiones_listar'),
    path('MA/preadmisiones/buscar', login_required(MAPreAdmisionesBuscarListView.as_view()), name='MA_preadmisiones_buscar'),
    path('MA/preadmisiones/eliminar/<pk>', login_required(MAPreAdmisionesDeleteView.as_view()), name='MA_preadmisiones_eliminar'),
    # Indice Ingreso
    path('MA/criterios_ingreso/crear', login_required(MACriteriosIngresoCreateView.as_view()), name='MA_criterios_ingreso_crear'),
    path('MA/indice_ingreso/crear/<pk>', login_required(MAIndiceIngresoCreateView.as_view()), name='MA_indiceingreso_crear'),
    #path('MA/indice_ivi_egreso/crear/<pk>', login_required(MAIndiceIviEgresoCreateView.as_view()), name='MA_indiceiviegreso_crear'),
    path('MA/indice_ingreso/ver/<pk>', login_required(MAIndiceIngresoDetailView.as_view()), name='MA_indiceingreso_ver'),
    path('MA/indice_ingreso/editar/<pk>', login_required(MAIndiceIngresoUpdateView.as_view()), name='MA_indiceingreso_editar'),
    # IVI
    path('MA/criterios_ivi/crear', login_required(MACriteriosIVICreateView.as_view()), name='MA_criterios_ivi_crear'),
    path('MA/indice_ivi/crear/<pk>', login_required(MAIndiceIviCreateView.as_view()), name='MA_indiceivi_crear'),
    path('MA/indice_ivi_egreso/crear/<pk>', login_required(MAIndiceIviEgresoCreateView.as_view()), name='MA_indiceiviegreso_crear'),
    path('MA/indice_ivi/ver/<pk>', login_required(MAIndiceIviDetailView.as_view()), name='MA_indiceivi_ver'),
    path('MA/indice_ivi/editar/<pk>', login_required(MAIndiceIviUpdateView.as_view()), name='MA_indiceivi_editar'),
    # Admisiones
    path('MA/admisiones/ver/<pk>', login_required(MAAdmisionesDetailView.as_view()), name='MA_admisiones_ver'),
    path('MA/admisiones/listar/', login_required(MAAdmisionesListView.as_view()), name='MA_admisiones_listar'),
    path('MA/admisiones/buscar', login_required(MAAdmisionesBuscarListView.as_view()), name='MA_admisiones_buscar'),
    path('MA/asignado_admisiones/ver/<pk>', login_required(MAAsignadoAdmisionDetail.as_view()), name='MA_asignado_admisiones_ver'),
    path('MA/inactiva_admisiones/ver/<pk>', login_required(MAInactivaAdmisionDetail.as_view()), name='MA_inactiva_admisiones_ver'),
    # Intervensiones
    path('MA/intervenciones/crear/<pk>', login_required(MAIntervencionesCreateView.as_view()), name='MA_intervenciones_crear'),
    path('MA/intervenciones/ver/<pk>', login_required(MAIntervencionesLegajosListView.as_view()), name='MA_intervenciones_legajos_listar'),
    path('MA/intervenciones/listar/', login_required(MAIntervencionesListView.as_view()), name='MA_intervenciones_listar'),
    path('MA/intervencion/ver/<pk>', login_required(MAIntervencionesDetail.as_view()), name='MA_intervencion_ver'),
    path('MA/intervenciones/editar/<pk>', login_required(MAIntervencionesUpdateView.as_view()), name='MA_intervencion_editar'),
    path('MA/intervenciones/borrar/<pk>', login_required(MAIntervencionesDeleteView.as_view()), name='MA_intervencion_borrar'),

    ]

