"""URLs de la API server-to-server con la Ticketera."""

from django.urls import path

from ticketera.api_views import (
    TicketeraAuthCambiarPasswordView,
    TicketeraAuthVerificarView,
    TicketeraSolicitarResetPasswordView,
    TicketeraUsuarioCreateView,
    TicketeraUsuarioUpdateView,
)


urlpatterns = [
    path(
        "usuarios/",
        TicketeraUsuarioCreateView.as_view(),
        name="ticketera-usuarios",
    ),
    path(
        "usuarios/<str:username>/",
        TicketeraUsuarioUpdateView.as_view(),
        name="ticketera-usuarios-detail",
    ),
    path(
        "auth/verificar/",
        TicketeraAuthVerificarView.as_view(),
        name="ticketera-auth-verificar",
    ),
    path(
        "auth/cambiar-password/",
        TicketeraAuthCambiarPasswordView.as_view(),
        name="ticketera-auth-cambiar-password",
    ),
    path(
        "auth/solicitar-reset-password/",
        TicketeraSolicitarResetPasswordView.as_view(),
        name="ticketera-auth-solicitar-reset-password",
    ),
]
