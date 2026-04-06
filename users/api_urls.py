from django.urls import include, path
from rest_framework.routers import DefaultRouter

from users.api_views import (
    PasswordChangeRequiredViewSet,
    PasswordResetConfirmViewSet,
    PasswordResetRequestViewSet,
    UserContextViewSet,
    UserLoginViewSet,
    UserLogoutViewSet,
)

router = DefaultRouter()
router.register(r"login", UserLoginViewSet, basename="api-user-login")
router.register(r"logout", UserLogoutViewSet, basename="api-user-logout")
router.register(r"me", UserContextViewSet, basename="api-user-context")
router.register(
    r"password-change-required",
    PasswordChangeRequiredViewSet,
    basename="api-user-password-change-required",
)
router.register(
    r"password-reset/request",
    PasswordResetRequestViewSet,
    basename="api-user-password-reset-request",
)
router.register(
    r"password-reset/confirm",
    PasswordResetConfirmViewSet,
    basename="api-user-password-reset-confirm",
)

urlpatterns = [
    path("", include(router.urls)),
]
