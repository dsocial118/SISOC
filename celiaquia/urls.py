# celiaquia/urls.py
from django.urls import path
from core.decorators import group_required

from celiaquia.views.expediente import (
    ExpedienteListView,
    ExpedienteCreateView,
    ExpedienteDetailView,
    ExpedienteUpdateView,
    ExpedientePreviewExcelView,
    ExpedienteImportView,
    ExpedienteConfirmView,
    AsignarTecnicoView,
    CrearLegajosView,
    ProcesarExpedienteView,
)
from celiaquia.views.legajo import LegajoArchivoUploadView


urlpatterns = [
    # Provincia: gestión básica de expedientes
    path(
        "expedientes/",
        group_required(["Provincia","CoordinadorCeliaquia"])(ExpedienteListView.as_view()),
        name="expediente_list",
    ),
    path(
        "expedientes/nuevo/",
        group_required(["Provincia"])(ExpedienteCreateView.as_view()),
        name="expediente_create",
    ),
    path(
        "expedientes/preview_excel/",
        group_required(["Provincia"])(ExpedientePreviewExcelView.as_view()),
        name="expediente_preview_excel",
    ),
    path(
        "expedientes/<int:pk>/",
        group_required(["Provincia","CoordinadorCeliaquia"])(ExpedienteDetailView.as_view()),
        name="expediente_detail",
    ),
    path(
        "expedientes/<int:pk>/editar/",
        group_required(["Provincia"])(ExpedienteUpdateView.as_view()),
        name="expediente_update",
    ),
    path(
        "expedientes/<int:pk>/importar/",
        group_required(["Provincia"])(ExpedienteImportView.as_view()),
        name="expediente_import",
    ),
    path(
        "expedientes/<int:pk>/procesar/",
        group_required(["Provincia"])(ProcesarExpedienteView.as_view()),
        name="expediente_procesar",
    ),
    path(
        "expedientes/<int:pk>/crear-legajos/",
        group_required(["Provincia"])(CrearLegajosView.as_view()),
        name="crear_legajos",
    ),
    path(
        "expedientes/<int:pk>/confirmar/",
        group_required(["Provincia"])(ExpedienteConfirmView.as_view()),
        name="expediente_confirm",
    ),
    path(
        "expedientes/<int:expediente_id>/ciudadanos/<int:pk>/archivo/",
        group_required(["Provincia"])(LegajoArchivoUploadView.as_view()),
        name="legajo_archivo_upload",
    ),
    # Coordinador Celiaquia: asignación de técnicos
    path('expedientes/<int:pk>/asignar-tecnico/', 
        group_required(["CoordinadorCeliaquia"])(AsignarTecnicoView.as_view()), name='expediente_asignar_tecnico'),
]
