from django.urls import path
from configuraciones.decorators import group_required
from celiaquia.views import (
    ExpedienteCreateView,
    ExpedienteDetailView,
    ExpedienteListView,
    ExpedienteUpdateView,
    ExpedienteConfirmarView,
    ExpedienteAsignarTecnicoView,
    ExpedienteDetallePagoView,
    FormularioCargarView,
    CruceArchivosUploadView,
    CruceResultadoConfirmarView,
    InformePagoCreateView,
)

urlpatterns = [
    path(
        "celiaquia/expedientes/listar",
        group_required(["Admin Ver Expedientes", "Técnico Ver Tareas Asignadas", "Provincia Ver Estado Pago"])(
            ExpedienteListView.as_view()
        ),
        name="celiaquia_expedientes_listar",
    ),
    path(
        "celiaquia/expedientes/crear",
        group_required(["Provincia Crear Expediente"])(ExpedienteCreateView.as_view()),
        name="celiaquia_expedientes_crear",
    ),
    path(
        "celiaquia/expedientes/<pk>",
        group_required([
            "Admin Ver Expedientes",
            "Técnico Ver Tareas Asignadas",
            "Provincia Ver Estado Pago",
            "Provincia Ver Lista Aprobados"
        ])(ExpedienteDetailView.as_view()),
        name="celiaquia_expedientes_detalle",
    ),
    path(
        "celiaquia/expedientes/<pk>/editar",
        group_required(["Provincia Cargar Formulario"])(ExpedienteUpdateView.as_view()),
        name="celiaquia_expedientes_editar",
    ),
    path(
        "celiaquia/expedientes/<pk>/confirmar",
        group_required(["Provincia Finalizar Expediente"])(ExpedienteConfirmarView.as_view()),
        name="celiaquia_expedientes_confirmar",
    ),
    path(
        "celiaquia/expedientes/<pk>/asignar",
        group_required(["Admin Asignar Técnico"])(ExpedienteAsignarTecnicoView.as_view()),
        name="celiaquia_expedientes_asignar",
    ),
    path(
        "celiaquia/expedientes/<pk>/formulario",
        group_required(["Provincia Cargar Formulario"])(FormularioCargarView.as_view()),
        name="celiaquia_expedientes_formulario",
    ),
    path(
        "celiaquia/expedientes/<pk>/cruce/cargar",
        group_required(["Técnico Subir Cruces"])(CruceArchivosUploadView.as_view()),
        name="celiaquia_cruce_archivos_subir",
    ),
    path(
        "celiaquia/expedientes/<pk>/cruce/validar",
        group_required(["Técnico Validar Resultado Cruce"])(CruceResultadoConfirmarView.as_view()),
        name="celiaquia_cruce_validar",
    ),
    path(
        "celiaquia/expedientes/<pk>/pago/detalle",
        group_required(["Provincia Ver Estado Pago"])(ExpedienteDetallePagoView.as_view()),
        name="celiaquia_expediente_pago_detalle",
    ),
    path(
        "celiaquia/expedientes/<pk>/pago/registrar",
        group_required(["Técnico Registrar Informe Pago"])(InformePagoCreateView.as_view()),
        name="celiaquia_pago_registrar",
    ),
    path('expedientes/<int:pk>/cargar-persona/', FormularioCargarView.as_view(), name='celiaquia_expedientes_cargar_persona'),
]
