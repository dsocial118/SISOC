from django.urls import path

from relevamientos.views.api_views import (
    PrimerSeguimientoApiView,
    RelevamientoApiView,
    SeguimientoApiView,
)

urlpatterns = [
    # TODO: Migrar a router DRF (estilo centrodefamilia).
    path(
        "api/relevamiento",
        RelevamientoApiView.as_view(),
        name="api_relevamiento",
    ),
    path(
        "api/relevamiento/primer-seguimiento",
        PrimerSeguimientoApiView.as_view(),
        name="api_primer_seguimiento",
    ),
    path(
        "api/relevamiento/seguimiento",
        SeguimientoApiView.as_view(),
        name="api_seguimiento",
    ),
]
