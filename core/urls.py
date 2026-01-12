from django.urls import path
from django.contrib.auth.decorators import login_required

from .views import (
    detalle_filtro_favorito,
    filtros_favoritos,
    inicio_view,
    load_localidad,
    load_municipios,
    load_organizaciones,
)

urlpatterns = [
    path("inicio/", login_required(inicio_view), name="inicio"),
    path(
        "ajax/load-municipios/",
        login_required(load_municipios),
        name="ajax_load_municipios",
    ),
    path(
        "ajax/load-localidades/",
        login_required(load_localidad),
        name="ajax_load_localidades",
    ),
    path(
        "ajax/load-organizaciones/",
        login_required(load_organizaciones),
        name="ajax_load_organizaciones",
    ),
    path(
        "ajax/filtros-favoritos/",
        login_required(filtros_favoritos),
        name="filtros_favoritos",
    ),
    path(
        "ajax/filtros-favoritos/<int:pk>/",
        login_required(detalle_filtro_favorito),
        name="detalle_filtro_favorito",
    ),
]
