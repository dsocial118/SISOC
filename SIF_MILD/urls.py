from django.urls import path
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from .views import *

urlpatterns = [
    # Derivaciones
    path('MILD/derivaciones/listar', login_required(MILDDerivacionesListView.as_view()), name='MILD_derivaciones_listar'),
    path('MILD/derivaciones/buscar', login_required(MILDDerivacionesBuscarListView.as_view()), name='MILD_derivaciones_buscar'),
    path('MILD/derivaciones/ver/<pk>', login_required(MILDDerivacionesDetailView.as_view()), name='MILD_derivaciones_ver'),
    path('MILD/derivaciones/editar/<pk>', login_required(MILDDerivacionesUpdateView.as_view()), name='MILD_derivaciones_editar'),
    path('MILD/derivaciones/rechazo/<pk>', login_required(MILDDerivacionesRechazo.as_view()), name='MILD_derivaciones_rechazo'),
    # PreAdmisiones
    path('MILD/preadmisiones/crear/<pk>', login_required(MILDPreAdmisionesCreateView.as_view()), name='MILD_preadmisiones_crear'),
    path('MILD/preadmisiones/editar/<pk>', login_required(MILDPreAdmisionesUpdateView.as_view()), name='MILD_preadmisiones_editar'),
    path('MILD/preadmisiones/ver/<pk>', login_required(MILDPreAdmisionesDetailView.as_view()), name='MILD_preadmisiones_ver'),
    path('MILD/preadmisiones/ver3/<pk>', login_required(MILDPreAdmisiones3DetailView.as_view()), name='MILD_preadmisiones_ver3'),
    path('MILD/preadmisiones/listar', login_required(MILDPreAdmisionesListView.as_view()), name='MILD_preadmisiones_listar'),
    path('MILD/preadmisiones/buscar', login_required(MILDPreAdmisionesBuscarListView.as_view()), name='MILD_preadmisiones_buscar'),
    path('MILD/preadmisiones/eliminar/<pk>', login_required(MILDPreAdmisionesDeleteView.as_view()), name='MILD_preadmisiones_eliminar'),
    # Indice Ingreso
    path('MILD/criterios_ingreso/crear', login_required(MILDCriteriosIngresoCreateView.as_view()), name='MILD_criterios_ingreso_crear'),
    path('MILD/indice_ingreso/crear/<pk>', login_required(MILDIndiceIngresoCreateView.as_view()), name='MILD_indiceingreso_crear'),
    #path('MILD/indice_ivi_egreso/crear/<pk>', login_required(MILDIndiceIviEgresoCreateView.as_view()), name='MILD_indiceiviegreso_crear'),
    path('MILD/indice_ingreso/ver/<pk>', login_required(MILDIndiceIngresoDetailView.as_view()), name='MILD_indiceingreso_ver'),
    path('MILD/indice_ingreso/editar/<pk>', login_required(MILDIndiceIngresoUpdateView.as_view()), name='MILD_indiceingreso_editar'),
    # IVI
    path('MILD/criterios_ivi/crear', login_required(MILDCriteriosIVICreateView.as_view()), name='MILD_criterios_ivi_crear'),
    path('MILD/indice_ivi/crear/<pk>', login_required(MILDIndiceIviCreateView.as_view()), name='MILD_indiceivi_crear'),
    path('MILD/indice_ivi_egreso/crear/<pk>', login_required(MILDIndiceIviEgresoCreateView.as_view()), name='MILD_indiceiviegreso_crear'),
    path('MILD/indice_ivi/ver/<pk>', login_required(MILDIndiceIviDetailView.as_view()), name='MILD_indiceivi_ver'),
    path('MILD/indice_ivi/editar/<pk>', login_required(MILDIndiceIviUpdateView.as_view()), name='MILD_indiceivi_editar'),
    # Admisiones
    path('MILD/admisiones/ver/<pk>', login_required(MILDAdmisionesDetailView.as_view()), name='MILD_admisiones_ver'),
    path('MILD/admisiones/listar/', login_required(MILDAdmisionesListView.as_view()), name='MILD_admisiones_listar'),
    path('MILD/admisiones/buscar', login_required(MILDAdmisionesBuscarListView.as_view()), name='MILD_admisiones_buscar'),
    path('MILD/asignado_admisiones/ver/<pk>', login_required(MILDAsignadoAdmisionDetail.as_view()), name='MILD_asignado_admisiones_ver'),
    path('MILD/inactiva_admisiones/ver/<pk>', login_required(MILDInactivaAdmisionDetail.as_view()), name='MILD_inactiva_admisiones_ver'),
    # Intervensiones
    path('MILD/intervenciones/crear/<pk>', login_required(MILDIntervencionesCreateView.as_view()), name='MILD_intervenciones_crear'),
    path('MILD/intervenciones/ver/<pk>', login_required(MILDIntervencionesLegajosListView.as_view()), name='MILD_intervenciones_legajos_listar'),
    path('MILD/intervenciones/listar/', login_required(MILDIntervencionesListView.as_view()), name='MILD_intervenciones_listar'),
    path('MILD/intervencion/ver/<pk>', login_required(MILDIntervencionesDetail.as_view()), name='MILD_intervencion_ver'),
    path('MILD/intervenciones/editar/<pk>', login_required(MILDIntervencionesUpdateView.as_view()), name='MILD_intervencion_editar'),
    path('MILD/intervenciones/borrar/<pk>', login_required(MILDIntervencionesDeleteView.as_view()), name='MILD_intervencion_borrar'),

    ]

