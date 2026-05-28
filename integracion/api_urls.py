"""URLs de la API de integración con sistemas externos."""

from django.urls import path

from integracion.api_views import (
    TicketeraAuthCambiarPasswordView,
    TicketeraAuthVerificarView,
    TicketeraUsuarioCreateView,
)


urlpatterns = [
    path(
        "ticketera/usuarios/",
        TicketeraUsuarioCreateView.as_view(),
        name="integracion-ticketera-usuarios",
    ),
    path(
        "ticketera/auth/verificar/",
        TicketeraAuthVerificarView.as_view(),
        name="integracion-ticketera-auth-verificar",
    ),
    path(
        "ticketera/auth/cambiar-password/",
        TicketeraAuthCambiarPasswordView.as_view(),
        name="integracion-ticketera-auth-cambiar-password",
    ),
]
