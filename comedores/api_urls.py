from django.urls import include, path
from rest_framework.routers import DefaultRouter

from comedores.api_views import ComedorDetailViewSet, NominaViewSet

router = DefaultRouter()
router.register(r"nomina", NominaViewSet, basename="api-nomina")
router.register(r"", ComedorDetailViewSet, basename="api-comedor")

urlpatterns = [
    path("", include(router.urls)),
]
