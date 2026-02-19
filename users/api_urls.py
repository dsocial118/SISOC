from django.urls import include, path
from rest_framework.routers import DefaultRouter

from users.api_views import UserContextViewSet, UserLoginViewSet, UserLogoutViewSet

router = DefaultRouter()
router.register(r"login", UserLoginViewSet, basename="api-user-login")
router.register(r"logout", UserLogoutViewSet, basename="api-user-logout")
router.register(r"me", UserContextViewSet, basename="api-user-context")

urlpatterns = [
    path("", include(router.urls)),
]
