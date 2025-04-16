from django.urls import path

from admisiones.views.web_views import (
    AdmisionesTecnicosListView,
    AdmisionesTecnicosCreateView,
    AdmisionesTecnicosUpdateView,
    subir_archivo_admision,
    eliminar_archivo_admision,
)

from comedores.views.web_views import sub_estados_intervenciones_ajax
from configuraciones.decorators import group_required

urlspatterns = [
    path(
        "comedores/admisiones/tecnicos/listar",
        group_required("Comedores")(AdmisionesTecnicosListView.as_view()),
        name="admisiones_tecnicos_listar",
    ),
    path(
        "comedores/admisiones/tecnicos/crear/<pk>",
        group_required("Comedores")(AdmisionesTecnicosCreateView.as_view()),
        name="admisiones_tecnicos_crear",
    ),
    path(
        "comedores/admisiones/tecnicos/editar/<pk>",
        group_required("Comedores")(AdmisionesTecnicosUpdateView.as_view()),
        name="admisiones_tecnicos_editar",
    ),
    path(
        "admision/<int:admision_id>/documentacion/<int:documentacion_id>/subir/",
        subir_archivo_admision,
        name="subir_archivo_admision",
    ),
    path(
        "admision/<int:admision_id>/documentacion/<int:documentacion_id>/eliminar/",
        eliminar_archivo_admision,
        name="eliminar_archivo_admision",
    ),
    path(
        "comedores/ajax/load-subestadosintervenciones/",
        sub_estados_intervenciones_ajax,
        name="ajax_load_subestadosintervenciones",
    ),
]
