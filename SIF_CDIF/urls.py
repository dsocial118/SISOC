from django.urls import path
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from .views import *

urlpatterns = [
    # Derivaciones
    path('CDIF/derivaciones/listar', login_required(CDIFDerivacionesListView.as_view()), name='CDIF_derivaciones_listar'),
    path('CDIF/derivaciones/buscar', login_required(CDIFDerivacionesBuscarListView.as_view()), name='CDIF_derivaciones_buscar'),
    path('CDIF/derivaciones/ver/<pk>', login_required(CDIFDerivacionesDetailView.as_view()), name='CDIF_derivaciones_ver'),
    path('CDIF/derivaciones/editar/<pk>', login_required(CDIFDerivacionesUpdateView.as_view()), name='CDIF_derivaciones_editar'),
    path('CDIF/derivaciones/rechazo/<pk>', login_required(CDIFDerivacionesRechazo.as_view()), name='CDIF_derivaciones_rechazo'),
    # PreAdmisiones
    path('CDIF/preadmisiones/crear/<pk>', login_required(CDIFPreAdmisionesCreateView.as_view()), name='CDIF_preadmisiones_crear'),
    path('CDIF/preadmisiones/editar/<pk>', login_required(CDIFPreAdmisionesUpdateView.as_view()), name='CDIF_preadmisiones_editar'),
    path('CDIF/preadmisiones/ver/<pk>', login_required(CDIFPreAdmisionesDetailView.as_view()), name='CDIF_preadmisiones_ver'),
    path('CDIF/preadmisiones/ver2/<pk>', login_required(CDIFPreAdmisiones2DetailView.as_view()), name='CDIF_preadmisiones_ver2'),
    path('CDIF/preadmisiones/ver3/<pk>', login_required(CDIFPreAdmisiones3DetailView.as_view()), name='CDIF_preadmisiones_ver3'),
    path('CDIF/preadmisiones/listar', login_required(CDIFPreAdmisionesListView.as_view()), name='CDIF_preadmisiones_listar'),
    path('CDIF/preadmisiones/buscar', login_required(CDIFPreAdmisionesBuscarListView.as_view()), name='CDIF_preadmisiones_buscar'),
    path('CDIF/preadmisiones/eliminar/<pk>', login_required(CDIFPreAdmisionesDeleteView.as_view()), name='CDIF_preadmisiones_eliminar'),
    # IVI
    path('CDIF/criterios_ivi/crear', login_required(CDIFCriteriosIVICreateView.as_view()), name='CDIF_criterios_ivi_crear'),
    path('CDIF/indice_ivi/crear/<pk>', login_required(CDIFIndiceIviCreateView.as_view()), name='CDIF_indiceivi_crear'),
    path('CDIF/indice_ivi_egreso/crear/<pk>', login_required(CDIFIndiceIviEgresoCreateView.as_view()), name='CDIF_indiceiviegreso_crear'),
    path('CDIF/indice_ivi/ver/<pk>', login_required(CDIFIndiceIviDetailView.as_view()), name='CDIF_indiceivi_ver'),
    path('CDIF/indice_ivi/editar/<pk>', login_required(CDIFIndiceIviUpdateView.as_view()), name='CDIF_indiceivi_editar'),
    # Vacantes
    path('CDIF/vacantes/list/', login_required(CDIFVacantesListView.as_view()), name='CDIF_vacantes_listar'),
    path('CDIF/vacantes/ver/<pk>', login_required(CDIFVacantesDetailView.as_view()), name='CDIF_vacantes_ver'),
    path('CDIF/vacantes/crear/<pk>', login_required(CDIFVacantesAdmision.as_view()), name='CDIF_vacantes_form'),
    path('CDIF/vacantes/cambio/<pk>', login_required(CDIFVacantesAdmisionCambio.as_view()), name='CDIF_vacantes_form_cambio'),
    # Admisiones
    path('CDIF/admisiones/ver/<pk>', login_required(CDIFAdmisionesDetailView.as_view()), name='CDIF_admisiones_ver'),
    path('CDIF/admisiones/listar/', login_required(CDIFAdmisionesListView.as_view()), name='CDIF_admisiones_listar'),
    path('CDIF/admisiones/buscar', login_required(CDIFAdmisionesBuscarListView.as_view()), name='CDIF_admisiones_buscar'),
    path('CDIF/asignado_admisiones/ver/<pk>', login_required(CDIFAsignadoAdmisionDetail.as_view()), name='CDIF_asignado_admisiones_ver'),
    path('CDIF/inactiva_admisiones/ver/<pk>', login_required(CDIFInactivaAdmisionDetail.as_view()), name='CDIF_inactiva_admisiones_ver'),
    # Intervensiones
    path('CDIF/intervenciones/crear/<pk>', login_required(CDIFIntervencionesCreateView.as_view()), name='CDIF_intervenciones_crear'),
    path('CDIF/intervenciones/ver/<pk>', login_required(CDIFIntervencionesLegajosListView.as_view()), name='CDIF_intervenciones_legajos_listar'),
    path('CDIF/intervenciones/listar/', login_required(CDIFIntervencionesListView.as_view()), name='CDIF_intervenciones_listar'),
    path('CDIF/intervencion/ver/<pk>', login_required(CDIFIntervencionesDetail.as_view()), name='CDIF_intervencion_ver'),
    path('CDIF/intervenciones/editar/<pk>', login_required(CDIFIntervencionesUpdateView.as_view()), name='CDIF_intervencion_editar'),
    path('CDIF/intervenciones/borrar/<pk>', login_required(CDIFIntervencionesDeleteView.as_view()), name='CDIF_intervencion_borrar'),

    ]

