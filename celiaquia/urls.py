
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
)
from celiaquia.views.legajo import LegajoArchivoUploadView


urlpatterns = [
    # Provincia
    path(
        'expedientes/',
        group_required(['Provincia'])(ExpedienteListView.as_view()),
        name='expediente_list'
    ),
    path(
        'expedientes/nuevo/',
        group_required(['Provincia'])(ExpedienteCreateView.as_view()),
        name='expediente_create'
    ),
    path(
        'expedientes/preview_excel/',
        ExpedientePreviewExcelView.as_view(),
        name='expediente_preview_excel'
    ),
    path(
        'expedientes/<int:pk>/',
        group_required(['Provincia'])(ExpedienteDetailView.as_view()),
        name='expediente_detail'
    ),
    path(
        'expedientes/<int:pk>/editar/',
        group_required(['Provincia'])(ExpedienteUpdateView.as_view()),
        name='expediente_update'
    ),
    path(
        'expedientes/<int:pk>/importar/',
        group_required(['Provincia'])(ExpedienteImportView.as_view()),
        name='expediente_import'
    ),
    path(
        'expedientes/<int:pk>/crear-legajos/',
        group_required(['Provincia'])(CrearLegajosView.as_view()),
        name='crear_legajos'
    ),
    path(
        'expedientes/<int:pk>/confirmar/',
        group_required(['Provincia'])(ExpedienteConfirmView.as_view()),
        name='expediente_confirm'
    ),
    path(
        'expedientes/<int:expediente_id>/ciudadanos/<int:pk>/archivo/',
        group_required(['Provincia'])(LegajoArchivoUploadView.as_view()),
        name='legajo_archivo_upload'
    ),

    # Coordinador
    path(
        'expedientes/<int:pk>/asignar/',
        group_required(['CoordinadorCeliaquia'])(AsignarTecnicoView.as_view()),
        name='expediente_asignar'
    ),
]
