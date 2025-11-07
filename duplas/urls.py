from django.urls import path
from core.decorators import group_required
from duplas.views import (
    DuplaCreateView,
    DuplaDeleteView,
    DuplaDetailView,
    DuplaListView,
    DuplaUpdateView,
)

urlpatterns = [
    path(
        "equipo-tecnico/",
        group_required(["Admin"])(DuplaListView.as_view()),
        name="dupla_list",
    ),
    path(
        "equipo-tecnico/crear/",
        group_required(["Admin"])(DuplaCreateView.as_view()),
        name="dupla_crear",
    ),
    path(
        "equipo-tecnico/<int:pk>/editar/",
        group_required(["Admin"])(DuplaUpdateView.as_view()),
        name="dupla_editar",
    ),
    path(
        "equipo-tecnico/<int:pk>/",
        group_required(["Admin"])(DuplaDetailView.as_view()),
        name="dupla_detalle",
    ),
    path(
        "equipo-tecnico/<int:pk>/eliminar/",
        group_required(["Admin"])(DuplaDeleteView.as_view()),
        name="dupla_eliminar",
    ),
]
