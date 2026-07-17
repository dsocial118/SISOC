from django.urls import include, path
from rest_framework.routers import DefaultRouter

from comedores.api_views_territorial import TerritorialComedorViewSet

router = DefaultRouter()
router.register(r"comedores", TerritorialComedorViewSet, basename="api-territorial-comedor")

urlpatterns = [
    path("", include(router.urls)),
]
