from django.urls import path

from relevamientos.views.api_views import (
    PrimerSeguimientoApiView,
    RelevamientoApiView,
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
]
