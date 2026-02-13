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
        group_required(["Gestor prestaciones"])(PrestacionListView.as_view()),
        name="prestacion",
    ),
    path(
        "prestacion/crear",
        group_required(["Gestor prestaciones"])(PrestacionCreateView.as_view()),
        name="prestacion_crear",
    ),
    path(
        "prestacion/<int:pk>/editar",
        group_required(["Gestor prestaciones"])(PrestacionUpdateView.as_view()),
        name="prestacion_editar",
    ),
    path(
        "prestacion/<int:pk>/eliminar",
        group_required(["Gestor prestaciones"])(PrestacionDeleteView.as_view()),
        name="prestacion_eliminar",
    ),
    path(
        "prestacion/<int:pk>/detalle",
        group_required(["Gestor prestaciones"])(PrestacionDetailView.as_view()),
        name="prestacion_detalle",
    ),
]
