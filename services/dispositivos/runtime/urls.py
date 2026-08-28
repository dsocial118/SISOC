"""Rutas internas del proceso de Dispositivos durante C2."""

from django.urls import include, path


urlpatterns = [
    path("", include("services.dispositivos.monolith_compat.app.urls")),
]
