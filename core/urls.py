from django.urls import path

from core.views import (
    changelog_view,
    columnas_preferencias,
    detalle_filtro_favorito,
    filtros_favoritos,
    inicio_view,
    load_localidad,
    load_municipios,
    load_organizaciones,
    MontoPrestacionProgramaListView,
    MontoPrestacionProgramaCreateView,
    MontoPrestacionProgramaUpdateView,
    MontoPrestacionProgramaDeleteView,
    MontoPrestacionProgramaDetailView,
)
from core.decorators import group_required

urlpatterns = [
    path("inicio/", inicio_view, name="inicio"),
    path("novedades/", changelog_view, name="changelog"),
    path(
        "ajax/load-municipios/",
        load_municipios,
        name="ajax_load_municipios",
    ),
    path(
        "ajax/load-localidades/",
        load_localidad,
        name="ajax_load_localidades",
    ),
    path(
        "ajax/load-organizaciones/",
        load_organizaciones,
        name="ajax_load_organizaciones",
    ),
    path(
        "ajax/filtros-favoritos/",
        filtros_favoritos,
        name="filtros_favoritos",
    ),
    path(
        "ajax/filtros-favoritos/<int:pk>/",
        detalle_filtro_favorito,
        name="detalle_filtro_favorito",
    ),
    path(
        "ajax/columnas-preferencias/",
        columnas_preferencias,
        name="column_preferences",
    ),
    path(
        "montoprestacion/listar",
        group_required(["Prestacion"])(MontoPrestacionProgramaListView.as_view()),
        name="montoprestacion_listar",
    ),
    path(
        "montoprestacion/crear",
        group_required(["Prestacion"])(MontoPrestacionProgramaCreateView.as_view()),
        name="montoprestacion_crear",
    ),
    path(
        "montoprestacion/<int:pk>/editar",
        group_required(["Prestacion"])(MontoPrestacionProgramaUpdateView.as_view()),
        name="montoprestacion_editar",
    ),
    path(
        "montoprestacion/<int:pk>/eliminar",
        group_required(["Prestacion"])(MontoPrestacionProgramaDeleteView.as_view()),
        name="montoprestacion_eliminar",
    ),
    path(
        "montoprestacion/<int:pk>/detalle",
        group_required(["Prestacion"])(MontoPrestacionProgramaDetailView.as_view()),
        name="montoprestacion_detalle",
    ),
]
