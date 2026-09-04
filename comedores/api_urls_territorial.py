from django.urls import include, path
from rest_framework.routers import DefaultRouter

from comedores.api_views_territorial import (
    MotivosExcepcionSeguimientoView,
    TerritorialComedorViewSet,
    TerritorialComedorZonaListView,
)

router = DefaultRouter()
router.register(
    r"comedores", TerritorialComedorViewSet, basename="api-territorial-comedor"
)

urlpatterns = [
    path(
        "catalogos/motivos-excepcion-seguimiento/",
        MotivosExcepcionSeguimientoView.as_view(),
        name="api-territorial-motivos-excepcion-seguimiento",
    ),
    path(
        "comedores-zona/",
        TerritorialComedorZonaListView.as_view(),
        name="api-territorial-comedores-zona",
    ),
    path("", include(router.urls)),
]
