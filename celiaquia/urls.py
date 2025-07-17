
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
from celiaquia.views.cruce import (
    CruceUploadView,
    CruceProcesarView,
    CruceFinalizarView,
)
from celiaquia.views.pago import OpenPaymentView, ClosePaymentView

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

    # Técnico
    path(
        'expedientes/<int:pk>/cruce/subir/',
        group_required(['Tecnico'])(CruceUploadView.as_view()),
        name='cruce_upload'
    ),
    path(
        'expedientes/<int:pk>/cruce/procesar/',
        group_required(['Tecnico'])(CruceProcesarView.as_view()),
        name='cruce_procesar'
    ),
    path(
        'expedientes/<int:pk>/cruce/finalizar/',
        group_required(['Tecnico'])(CruceFinalizarView.as_view()),
        name='cruce_finalizar'
    ),

    # Finanzas
    path(
        'expedientes/<int:pk>/pago/abrir/',
        group_required(['Finanzas'])(OpenPaymentView.as_view()),
        name='pago_open'
    ),
    path(
        'expedientes/<int:pk>/pago/cerrar/',
        group_required(['Finanzas'])(ClosePaymentView.as_view()),
        name='pago_close'
    ),
]
