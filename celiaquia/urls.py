from django.urls import path
from celiaquia.views.expediente_subsanacion import ExpedienteConfirmSubsanacionView
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
    RecepcionarExpedienteView,
    RevisarLegajoView,
    SubirCruceExcelView,
)

from celiaquia.views.confirm_envio import ExpedienteConfirmView
from celiaquia.views.legajo import LegajoArchivoUploadView, LegajoSubsanarView

from celiaquia.views.cupo import (
    CupoDashboardView,
    CupoProvinciaDetailView,
    CupoBajaLegajoView,
    CupoReactivarLegajoView,
    CupoSuspenderLegajoView,
)

urlpatterns = [
    path(
        "expedientes/<int:pk>/legajos/<int:legajo_id>/revisar/",
        RevisarLegajoView.as_view(),
        name="legajo_revisar"
    ),
    path(
        "expedientes/<int:pk>/legajos/<int:legajo_id>/subsanar/",
        group_required(["TecnicoCeliaquia", "CoordinadorCeliaquia"])(LegajoSubsanarView.as_view()),
        name="legajo_subsanar",
    ),

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
        group_required(["ProvinciaCeliaquia"])(ExpedientePreviewExcelView.as_view()),
        name="expediente_preview_excel",
    ),
    path(
        "expedientes/<int:pk>/",
        group_required(["ProvinciaCeliaquia", "CoordinadorCeliaquia", "TecnicoCeliaquia"])(
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
    path(
        "expedientes/<int:pk>/cruce-cuit/",
        group_required(["TecnicoCeliaquia"])(SubirCruceExcelView.as_view()),
        name="expediente_cruce_cuit",
    ),
    path(
        "expedientes/<int:pk>/cruce/",
        SubirCruceExcelView.as_view(),
        name="expediente_subir_cruce",
    ),

    path(
        "cupos/",
        group_required(["CoordinadorCeliaquia"])(CupoDashboardView.as_view()),
        name="cupo_dashboard",
    ),
    path(
        "cupos/provincia/<int:provincia_id>/",
        group_required(["CoordinadorCeliaquia"])(CupoProvinciaDetailView.as_view()),
        name="cupo_provincia_detail",
    ),
    path(
        "cupos/provincia/<int:provincia_id>/legajo/<int:legajo_id>/baja/",
        group_required(["CoordinadorCeliaquia"])(CupoBajaLegajoView.as_view()),
        name="cupo_legajo_baja",
    ),
    path(
        "cupos/provincia/<int:provincia_id>/legajo/<int:legajo_id>/suspender/",
        group_required(["CoordinadorCeliaquia"])(CupoSuspenderLegajoView.as_view()),
        name="cupo_legajo_suspender",
    ),
    path(
        "expedientes/<int:pk>/confirmar-subsanacion/",
        ExpedienteConfirmSubsanacionView.as_view(),
        name="expediente_confirm_subsanacion",
    ),

        path(
        "cupo/<int:provincia_id>/legajo/<int:legajo_id>/reactivar/",
        CupoReactivarLegajoView.as_view(),
        name="cupo_legajo_reactivar",
    ),
]
