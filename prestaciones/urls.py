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
        "prestaciones/listar",
        group_required(["Prestaciones"])(PrestacionListView.as_view()),
        name="prestaciones",
    ),
    path(
        "prestaciones/crear",
        group_required(["Prestaciones"])(PrestacionCreateView.as_view()),
        name="prestacion_crear",
    ),
    path(
        "prestaciones/<int:pk>/editar",
        group_required(["Prestaciones"])(PrestacionUpdateView.as_view()),
        name="prestacion_editar",
    ),
    path(
        "prestaciones/<int:pk>/eliminar",
        group_required(["Prestaciones"])(PrestacionDeleteView.as_view()),
        name="prestacion_eliminar",
    ),
    path(
        "prestaciones/<int:pk>/detalle",
        group_required(["Prestaciones"])(PrestacionDetailView.as_view()),
        name="prestacion_detalle",
     ),
]
