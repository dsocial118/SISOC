from django.urls import path
from core.decorators import group_required
from admisiones.views.web_views import (
    subir_archivo_admision,
    eliminar_archivo_admision,
    actualizar_estado_archivo,
    actualizar_numero_gde_archivo,
    crear_documento_personalizado,
    AdmisionesTecnicosListView,
    AdmisionesTecnicosUpdateView,
    AdmisionDetailView,
    InformeTecnicosCreateView,
    InformeTecnicosUpdateView,
    InformeTecnicoDetailView,
    InformeTecnicoComplementarioDetailView,
    InformeTecnicoComplementarioReviewView,
    AdmisionesLegalesListView,
    AdmisionesLegalesDetailView,
    admisiones_legales_ajax,
)

urlpatterns = [
    path(
        "comedores/admisiones/tecnicos/listar",
        group_required(["Comedores", "Tecnico Comedor", "Abogado Dupla", "Coordinador Gestion"])(
            AdmisionesTecnicosListView.as_view()
        ),
        name="admisiones_tecnicos_listar",
    ),
    path(
        "comedores/admisiones/tecnicos/editar/<int:pk>",
        group_required(["Comedores", "Tecnico Comedor", "Abogado Dupla", "Coordinador Gestion"])(
            AdmisionesTecnicosUpdateView.as_view()
        ),
        name="admisiones_tecnicos_editar",
    ),
    path(
        "comedores/<int:comedor_pk>/admision/<int:pk>/detalle/",
        group_required(["Comedores", "Tecnico Comedor", "Abogado Dupla", "Coordinador Gestion"])(
            AdmisionDetailView.as_view()
        ),
        name="admision_detalle",
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
        "admision/<int:admision_id>/documentacion/personalizada/agregar/",
        crear_documento_personalizado,
        name="documento_personalizado_crear",
    ),
    path(
        "comedores/admision/informe_tecnico/<str:tipo>/<int:admision_id>/crear/",
        group_required(["Comedores", "Tecnico Comedor"])(
            InformeTecnicosCreateView.as_view()
        ),
        name="informe_tecnico_crear",
    ),
    path(
        "comedores/admision/informe_tecnico/<str:tipo>/<int:pk>/editar/",
        group_required(["Comedores", "Tecnico Comedor"])(
            InformeTecnicosUpdateView.as_view()
        ),
        name="informe_tecnico_editar",
    ),
    path(
        "comedores/admision/informe_tecnico/<str:tipo>/<int:pk>/ver/",
        group_required(["Comedores", "Tecnico Comedor", "Abogado Dupla"])(
            InformeTecnicoDetailView.as_view()
        ),
        name="informe_tecnico_ver",
    ),
    path(
        "comedores/admision/informe_complementario/<str:tipo>/<int:pk>/ver/",
        group_required(["Comedores", "Tecnico Comedor", "Abogado Dupla"])(
            InformeTecnicoComplementarioDetailView.as_view()
        ),
        name="informe_complementario_ver",
    ),
    path(
        "ajax/actualizar-estado/",
        actualizar_estado_archivo,
        name="actualizar_estado_archivo",
    ),
    path(
        "ajax/actualizar-numero-gde/",
        actualizar_numero_gde_archivo,
        name="actualizar_numero_gde_archivo",
    ),
    # Legales
    path(
        "comedores/admisiones/legales/listar",
        group_required(["Area Legales"])(AdmisionesLegalesListView.as_view()),
        name="admisiones_legales_listar",
    ),
    path(
        "comedores/admisiones/legales/ver/<int:pk>",
        group_required(["Area Legales"])(AdmisionesLegalesDetailView.as_view()),
        name="admisiones_legales_ver",
    ),
    path(
        "comedores/admisiones/legales/revisar-complementario/<int:pk>",
        group_required(["Area Legales"])(
            InformeTecnicoComplementarioReviewView.as_view()
        ),
        name="revisar_informe_complementario",
    ),
    # AJAX endpoints
    path(
        "comedores/admisiones/legales/ajax/",
        admisiones_legales_ajax,
        name="admisiones_legales_ajax",
    ),
]
