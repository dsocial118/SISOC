from django.urls import include, path
from rest_framework.routers import DefaultRouter

from users.api_views import UserContextViewSet

router = DefaultRouter()
router.register(r"me", UserContextViewSet, basename="api-user-context")

urlpatterns = [
    path("", include(router.urls)),
]
