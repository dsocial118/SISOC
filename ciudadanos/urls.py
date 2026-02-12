from django.contrib.auth.decorators import login_required
from django.urls import path

from ciudadanos.views import (
    CiudadanosCreateView,
    CiudadanosDeleteView,
    CiudadanosDetailView,
    CiudadanosListView,
    CiudadanosUpdateView,
    GrupoFamiliarCreateView,
    GrupoFamiliarDeleteView,
)
from ciudadanos.api_views import buscar_ciudadanos
from ciudadanos.views_export import CiudadanosExportView


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
]
