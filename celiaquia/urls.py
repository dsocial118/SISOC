from django.urls import path
from core.decorators import group_required

from celiaquia.views.expediente import (
    ExpedienteListView,
    ExpedienteCreateView,
    ExpedienteDetailView,
    ExpedienteUpdateView,
    ExpedientePreviewExcelView,
    ExpedienteImportView,
    AsignarTecnicoView,
    CrearLegajosView,
    ProcesarExpedienteView,
    # ⬇️ NUEVO: importamos la vista de recepción (Coordinador)
    RecepcionarExpedienteView,
)
# Esta vista de confirmación sigue viniendo del módulo dedicado
from celiaquia.views.confirm_envio import ExpedienteConfirmView

from celiaquia.views.legajo import LegajoArchivoUploadView


urlpatterns = [
    # ProvinciaCeliaquia: gestión básica de expedientes
    path(
        "expedientes/",
        group_required(["ProvinciaCeliaquia", "CoordinadorCeliaquia", "TecnicoCeliaquia"])(
            ExpedienteListView.as_view()
        ),
        name="expediente_list",
    ),
    path(
        "expedientes/nuevo/",
        group_required(["ProvinciaCeliaquia"])(ExpedienteCreateView.as_view()),
        name="expediente_create",
    ),
    path(
        "expedientes/preview_excel/",
        group_required(["ProvinciaCeliaquia"])(
            ExpedientePreviewExcelView.as_view()
        ),
        name="expediente_preview_excel",
    ),
    path(
        "expedientes/<int:pk>/",
        group_required(["ProvinciaCeliaquia", "CoordinadorCeliaquia"])(
            ExpedienteDetailView.as_view()
        ),
        name="expediente_detail",
    ),
    path(
        "expedientes/<int:pk>/editar/",
        group_required(["ProvinciaCeliaquia"])(ExpedienteUpdateView.as_view()),
        name="expediente_update",
    ),
    path(
        "expedientes/<int:pk>/importar/",
        group_required(["ProvinciaCeliaquia"])(ExpedienteImportView.as_view()),
        name="expediente_import",
    ),
    path(
        "expedientes/<int:pk>/procesar/",
        group_required(["ProvinciaCeliaquia"])(ProcesarExpedienteView.as_view()),
        name="expediente_procesar",
    ),
    path(
        "expedientes/<int:pk>/crear-legajos/",
        group_required(["ProvinciaCeliaquia"])(CrearLegajosView.as_view()),
        name="crear_legajos",
    ),
    path(
        "expedientes/<int:pk>/confirmar/",
        group_required(["ProvinciaCeliaquia"])(ExpedienteConfirmView.as_view()),
        name="expediente_confirm",
    ),
    path(
        "expedientes/<int:expediente_id>/ciudadanos/<int:pk>/archivo/",
        group_required(["ProvinciaCeliaquia"])(LegajoArchivoUploadView.as_view()),
        name="legajo_archivo_upload",
    ),

    # Coordinador Celiaquia: recepción y asignación de técnicos
    path(
        "expedientes/<int:pk>/recepcionar/",
        group_required(["CoordinadorCeliaquia"])(RecepcionarExpedienteView.as_view()),
        name="expediente_recepcionar",
    ),
    path(
        "expedientes/<int:pk>/asignar-tecnico/",
        group_required(["CoordinadorCeliaquia"])(AsignarTecnicoView.as_view()),
        name="expediente_asignar_tecnico",
    ),
]
