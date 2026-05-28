"""URLs de la API server-to-server con la Ticketera."""

from django.urls import path

from ticketera.api_views import (
    TicketeraAuthCambiarPasswordView,
    TicketeraAuthVerificarView,
    TicketeraUsuarioCreateView,
)


urlpatterns = [
    path(
        "usuarios/",
        TicketeraUsuarioCreateView.as_view(),
        name="ticketera-usuarios",
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
]
