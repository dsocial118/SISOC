from django.urls import path
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from .views import *
from debug_toolbar.toolbar import debug_toolbar_urls

urlpatterns = [
    path('dashboard/', login_required(DashboardView.as_view()), name='dashboard'),
    path('metricas/', login_required(TemplateView.as_view(template_name='metricas.html')), name='metricas'),
    path('busqueda/menu', login_required(BusquedaMenu.as_view()), name='busqueda_menu'),
    # Plantilla Ejemplos
    path('plantilla/ejemplos/500', login_required(TemplateView.as_view(template_name='Ejemplos/500.html')), name='500'),
    path('plantilla/ejemplos/404', login_required(TemplateView.as_view(template_name='Ejemplos/404.html')), name='404'),
    path('plantilla/ejemplos/403', login_required(TemplateView.as_view(template_name='Ejemplos/403.html')), name='403'),
    path('plantilla/ejemplos/formularios', login_required(TemplateView.as_view(template_name='Ejemplos/formularios.html')), name='formularios'),
    path('plantilla/ejemplos/steps', login_required(TemplateView.as_view(template_name='Ejemplos/steps.html')), name='steps'),
    path('plantilla/ejemplos/vista_detalle_doble', login_required(TemplateView.as_view(template_name='Ejemplos/vista_detalle_doble.html')), name='vista_detalle_doble'),
    path('plantilla/ejemplos/vista_detalle_simple', login_required(TemplateView.as_view(template_name='Ejemplos/vista_detalle_simple.html')), name='vista_detalle_simple'),
    path('plantilla/ejemplos/vista_detalle_desplegable', login_required(TemplateView.as_view(template_name='Ejemplos/vista_detalle_desplegable.html')), name='vista_detalle_desplegable'),
    path('plantilla/ejemplos/tablas', login_required(TemplateView.as_view(template_name='Ejemplos/tablas.html')), name='tablas'),
    path('plantilla/ejemplos/confirm_delete', login_required(TemplateView.as_view(template_name='Ejemplos/confirm_delete.html')), name='confirm_delete'),
    path('plantilla/ejemplos/timelineh', login_required(TemplateView.as_view(template_name='Ejemplos/timelineh.html')), name='timelineh'),
    path('plantilla/ejemplos/timelineh2', login_required(TemplateView.as_view(template_name='Ejemplos/timelineh2.html')), name='timelineh2'),
    # Plantilla Legajos
    path('plantilla/legajos/busqueda_legajo', login_required(TemplateView.as_view(template_name='Ejemplos/busqueda_legajo.html')), name='busqueda_legajo'),
    path('plantilla/legajos/grupo_familiar', login_required(TemplateView.as_view(template_name='Ejemplos/grupo_familiar.html')), name='grupo_familiar'),
    path('plantilla/legajos/programas_interviniendo', login_required(TemplateView.as_view(template_name='Ejemplos/programas_interviniendo.html')), name='programas_interviniendo'),
    # Plantilla Programas Derivaciones
    path('plantilla/programas/derivaciones_historial', login_required(TemplateView.as_view(template_name='Ejemplos/derivaciones_historial.html')), name='derivaciones_historial'),
    path('plantilla/programas/derivaciones_buscar', login_required(TemplateView.as_view(template_name='Ejemplos/derivaciones_buscar.html')), name='derivaciones_buscar'),
    path('plantilla/programas/derivaciones_form', login_required(TemplateView.as_view(template_name='Ejemplos/derivaciones_form.html')), name='derivaciones_form'),
    path('plantilla/programas/derivaciones_detail', login_required(TemplateView.as_view(template_name='Ejemplos/derivaciones_detail.html')), name='derivaciones_detail'),
    path('plantilla/programas/derivaciones_con_motivo', login_required(TemplateView.as_view(template_name='Ejemplos/derivaciones_con_motivo.html')), name='derivaciones_con_motivo'),
    path('plantilla/programas/derivaciones_bandeja', login_required(TemplateView.as_view(template_name='Ejemplos/derivaciones_bandeja.html')), name='derivaciones_bandeja'),
    # Plantilla Programas Indice
    path('plantilla/programas/indice_ivi_form', login_required(TemplateView.as_view(template_name='Ejemplos/indice_ivi_form.html')), name='indice_ivi_form'),
    path('plantilla/programas/indice_ivi_formegreso', login_required(TemplateView.as_view(template_name='Ejemplos/indice_ivi_formegreso.html')), name='indice_ivi_formegreso'),
    path('plantilla/programas/indice_ivi_detail', login_required(TemplateView.as_view(template_name='Ejemplos/indice_ivi_detail.html')), name='indice_ivi_detail'),
    path('plantilla/programas/indice_ivi_form2', login_required(TemplateView.as_view(template_name='Ejemplos/indice_ivi_form2.html')), name='indice_ivi_form2'),
    # Plantilla Programas Pre-admisiones
    path('plantilla/programas/preadmisiones_list', login_required(TemplateView.as_view(template_name='Ejemplos/preadmisiones_list.html')), name='preadmisiones_list'),
    path('plantilla/programas/preadmisiones_buscar', login_required(TemplateView.as_view(template_name='Ejemplos/preadmisiones_buscar.html')), name='preadmisiones_buscar'),
    path('plantilla/programas/preadmisiones_form', login_required(TemplateView.as_view(template_name='Ejemplos/preadmisiones_form.html')), name='preadmisiones_form'),
    path('plantilla/programas/preadmisiones_detail', login_required(TemplateView.as_view(template_name='Ejemplos/preadmisiones_detail.html')), name='preadmisiones_detail'),
    path('plantilla/programas/preadmisiones_detail2', login_required(TemplateView.as_view(template_name='Ejemplos/preadmisiones_detail2.html')), name='preadmisiones_detail2'),
    path('plantilla/programas/preadmisiones_detail3', login_required(TemplateView.as_view(template_name='Ejemplos/preadmisiones_detail3.html')), name='preadmisiones_detail3'),
    path('plantilla/programas/preadmisiones_form_legajo', login_required(TemplateView.as_view(template_name='Ejemplos/preadmisiones_form_legajo.html')), name='preadmisiones_form_legajo'),
    # Vacantes
    path('plantilla/programas/vacantes_form', login_required(TemplateView.as_view(template_name='Ejemplos/vacantes_form.html')), name='vacantes_form'),
    path('plantilla/programas/vacantes_form_cambio', login_required(TemplateView.as_view(template_name='Ejemplos/vacantes_form_cambio.html')), name='vacantes_form_cambio'),
    path('plantilla/programas/vacantes_list', login_required(TemplateView.as_view(template_name='Ejemplos/vacantes_list.html')), name='vacantes_list'),
    path('plantilla/programas/vacantesxcentro', login_required(TemplateView.as_view(template_name='Ejemplos/vacantesxcentro.html')), name='vacantesxcentro'),
    # Plantilla Programas admisiones
    path('plantilla/programas/admisiones_historial', login_required(TemplateView.as_view(template_name='Ejemplos/admisiones_historial.html')), name='admisiones_historial'),
    path('plantilla/programas/admisiones_form1', login_required(TemplateView.as_view(template_name='Ejemplos/admisiones_form1.html')), name='admisiones_form1'),
    path('plantilla/programas/admisiones_form', login_required(TemplateView.as_view(template_name='Ejemplos/admisiones_form.html')), name='admisiones_form'),
    path('plantilla/programas/admisiones_list', login_required(TemplateView.as_view(template_name='Ejemplos/admisiones_list.html')), name='admisiones_list'),
    path('plantilla/programas/admisiones_detail', login_required(TemplateView.as_view(template_name='Ejemplos/admisiones_detail.html')), name='admisiones_detail'),
    path('plantilla/programas/vacantes_detail', login_required(TemplateView.as_view(template_name='Ejemplos/vacantes_detail.html')), name='vacantes_detail'),
    path('plantilla/programas/admisiones_detail_inactiva', login_required(TemplateView.as_view(template_name='Ejemplos/admisiones_detail_inactiva.html')), name='admisiones_detail_inactiva'),
    # Plantilla Programas de asistencia
    path('plantilla/programas/programas_asistencia', login_required(TemplateView.as_view(template_name='Ejemplos/programas_asistencia.html')), name='programas_asistencia'),
    # Plantilla Intervenciones de Salud
    path('plantilla/programas/intervenciones_salud', login_required(TemplateView.as_view(template_name='Ejemplos/intervenciones_salud.html')), name='intervenciones_salud'),
    # Plantilla Acciones sociales
    path('plantilla/programas/acciones_sociales', login_required(TemplateView.as_view(template_name='Ejemplos/acciones_sociales.html')), name='acciones_sociales'),
     # Plantilla Indices
    path('plantilla/programas/indices', login_required(TemplateView.as_view(template_name='Ejemplos/indices.html')), name='indices'),
    path('plantilla/programas/indices_egreso', login_required(TemplateView.as_view(template_name='Ejemplos/indices_egreso.html')), name='indices_egreso'),
     # Plantilla Intervenciones
    path('plantilla/programas/intervenciones', login_required(TemplateView.as_view(template_name='Ejemplos/intervenciones.html')), name='intervenciones'),
    path('plantilla/programas/intervenciones_new_detail', login_required(TemplateView.as_view(template_name='Ejemplos/intervenciones_new_detail.html')), name='intervenciones_new_detail'),
     # Plantilla Historial de admisiones
    path('plantilla/programas/historial_admisiones', login_required(TemplateView.as_view(template_name='Ejemplos/historial_admisiones.html')), name='historial_admisiones'),
    # Plantilla Derivaciones
    path('plantilla/programas/historial_derivaciones', login_required(TemplateView.as_view(template_name='Ejemplos/historial_derivaciones.html')), name='historial_derivaciones'),
    path('plantilla/programas/derivaciones_new_detail', login_required(TemplateView.as_view(template_name='Ejemplos/derivaciones_new_detail.html')), name='derivaciones_new_detail'),
    # Plantilla Programas Indice
    path('plantilla/programas/indice_ivi_legajo', login_required(TemplateView.as_view(template_name='Ejemplos/indice_ivi_legajo.html')), name='indice_ivi_legajo'),
    path('plantilla/programas/indice_ivi_form_legajo', login_required(TemplateView.as_view(template_name='Ejemplos/indice_ivi_form_legajo.html')), name='indice_ivi_form_legajo'),
    # Intervenciones
    path('plantilla/programas/intervenciones_legajolist', login_required(TemplateView.as_view(template_name='Ejemplos/intervenciones_legajolist.html')), name='intervenciones_legajolist'),
    path('plantilla/programas/intervenciones_list', login_required(TemplateView.as_view(template_name='Ejemplos/intervenciones_list.html')), name='intervenciones_list'),
    path('plantilla/programas/intervenciones_form', login_required(TemplateView.as_view(template_name='Ejemplos/intervenciones_form.html')), name='intervenciones_form'),
    path('plantilla/programas/intervenciones_detail', login_required(TemplateView.as_view(template_name='Ejemplos/intervenciones_detail.html')), name='intervenciones_detail'),
    # Intervenciones salud HC
    path('plantilla/programas/intervenciones_salud_HC', login_required(TemplateView.as_view(template_name='Ejemplos/intervenciones_salud_HC.html')), name='intervenciones_salud_HC'),
    # CDIF reportes
    path('plantilla/programas/cdif_reportes', login_required(TemplateView.as_view(template_name='Ejemplos/cdif_reportes.html')), name='cdif_reportes'),
] + debug_toolbar_urls()