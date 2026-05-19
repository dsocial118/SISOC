from django.contrib.auth.decorators import login_required
from django.urls import path

from ciudadanos.views import (
    CiudadanosCreateView,
    CiudadanosDeleteView,
    CiudadanosDetailView,
    CiudadanosListView,
    CiudadanosUpdateView,
    ColaRevisionView,
    GrupoFamiliarCreateView,
    GrupoFamiliarDeleteView,
    descartar_revision,
    marcar_revisado,
)
from ciudadanos.api_views import buscar_ciudadanos
from ciudadanos.views_export import CiudadanosExportView
from ciudadanos.views_importacion_masiva import (
    CiudadanosImportJobDetailView,
    CiudadanosImportJobExportView,
    CiudadanosImportJobResumeView,
    CiudadanosImportTemplateView,
    CiudadanosImportUploadView,
)


urlpatterns = [
    path(
        "ciudadanos/listar",
        login_required(CiudadanosListView.as_view()),
        name="ciudadanos",
    ),
    path(
        "ciudadanos/exportar",
        login_required(CiudadanosExportView.as_view()),
        name="ciudadanos_exportar",
    ),
    path(
        "ciudadanos/importacion-masiva/",
        login_required(CiudadanosImportUploadView.as_view()),
        name="ciudadanos_importacion_masiva",
    ),
    path(
        "ciudadanos/importacion-masiva/plantilla/",
        login_required(CiudadanosImportTemplateView.as_view()),
        name="ciudadanos_importacion_masiva_plantilla",
    ),
    path(
        "ciudadanos/importacion-masiva/lotes/<int:pk>/",
        login_required(CiudadanosImportJobDetailView.as_view()),
        name="ciudadanos_importacion_masiva_lote",
    ),
    path(
        "ciudadanos/importacion-masiva/lotes/<int:pk>/exportar/",
        login_required(CiudadanosImportJobExportView.as_view()),
        name="ciudadanos_importacion_masiva_lote_exportar",
    ),
    path(
        "ciudadanos/importacion-masiva/lotes/<int:pk>/reanudar/",
        login_required(CiudadanosImportJobResumeView.as_view()),
        name="ciudadanos_importacion_masiva_reanudar",
    ),
    path(
        "ciudadanos/crear/",
        login_required(CiudadanosCreateView.as_view()),
        name="ciudadanos_crear",
    ),
    path(
        "ciudadanos/ver/<int:pk>",
        login_required(CiudadanosDetailView.as_view()),
        name="ciudadanos_ver",
    ),
    path(
        "ciudadanos/editar/<int:pk>",
        login_required(CiudadanosUpdateView.as_view()),
        name="ciudadanos_editar",
    ),
    path(
        "ciudadanos/eliminar/<int:pk>",
        login_required(CiudadanosDeleteView.as_view()),
        name="ciudadanos_eliminar",
    ),
    path(
        "ciudadanos/<int:pk>/familiares/nuevo",
        login_required(GrupoFamiliarCreateView.as_view()),
        name="grupofamiliar_crear",
    ),
    path(
        "ciudadanos/familiares/<int:pk>/eliminar",
        login_required(GrupoFamiliarDeleteView.as_view()),
        name="grupofamiliar_eliminar",
    ),
    path(
        # TODO: Migrar a router DRF (estilo centrodefamilia).
        "api/ciudadanos/buscar/",
        login_required(buscar_ciudadanos),
        name="api_buscar_ciudadanos",
    ),
    path(
        "ciudadanos/revision/",
        login_required(ColaRevisionView.as_view()),
        name="ciudadanos_cola_revision",
    ),
    path(
        "ciudadanos/<int:pk>/marcar-revisado/",
        marcar_revisado,
        name="ciudadanos_marcar_revisado",
    ),
    path(
        "ciudadanos/<int:pk>/descartar-revision/",
        descartar_revision,
        name="ciudadanos_descartar_revision",
    ),
]
