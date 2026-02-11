from django.urls import path

from core.decorators import group_required
from prestaciones.views import (
    PrestacionListView,
    PrestacionCreateView,
    PrestacionUpdateView,
    PrestacionDeleteView,
    PrestacionDetailView,
)

urlpatterns = [
    path(
        "prestacion/listar",
        group_required(["Prestacion"])(PrestacionListView.as_view()),
        name="prestacion",
    ),
    path(
        "prestacion/crear",
        group_required(["Prestacion"])(PrestacionCreateView.as_view()),
        name="prestacion_crear",
    ),
    path(
        "prestacion/<int:pk>/editar",
        group_required(["Prestacion"])(PrestacionUpdateView.as_view()),
        name="prestacion_editar",
    ),
    path(
        "prestacion/<int:pk>/eliminar",
        group_required(["Prestacion"])(PrestacionDeleteView.as_view()),
        name="prestacion_eliminar",
    ),
    path(
        "prestacion/<int:pk>/detalle",
        group_required(["Prestacion"])(PrestacionDetailView.as_view()),
        name="prestacion_detalle",
    ),
]
