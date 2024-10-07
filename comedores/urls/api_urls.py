from django.urls import path

from comedores.views.api_views import (
    ComedorRelevamientoObservacionApiView,
    ComedorApiView,
    RelevamientoApiView,
    ObservacionApiView,
)

urlpatterns = [
    path(
        "api/comedor-relevamiento-observacion",
        ComedorRelevamientoObservacionApiView.as_view(),
        name="api_comedor_relevamiento_observacion",
    ),
    path(
        "api/comedor",
        ComedorApiView.as_view(),
        name="api_comedor",
    ),
    path(
        "api/relevamiento",
        RelevamientoApiView.as_view(),
        name="api_relevamiento",
    ),
    path(
        "api/observacion",
        ObservacionApiView.as_view(),
        name="api_observacion",
    ),
]
