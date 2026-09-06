from django.urls import include, path
from rest_framework.routers import DefaultRouter

from datacalle.api_views import (
    CatalogoViewSet,
    EncuestaViewSet,
    RelevamientoViewSet,
)

router = DefaultRouter()
router.register(
    r"relevamientos", RelevamientoViewSet, basename="api-datacalle-relevamientos"
)
router.register(r"encuestas", EncuestaViewSet, basename="api-datacalle-encuestas")
router.register(r"catalogos", CatalogoViewSet, basename="api-datacalle-catalogos")

urlpatterns = [
    path("", include(router.urls)),
]
