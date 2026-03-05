from django.urls import path
from core.decorators import permissions_any_required
from duplas.views import (
    DuplaCreateView,
    DuplaDeleteView,
    DuplaDetailView,
    DuplaListView,
    DuplaUpdateView,
)
from duplas.views_export import DuplaExportView


urlpatterns = [
    path(
        "equipo-tecnico/",
        permissions_any_required(["Admin"])(DuplaListView.as_view()),
        name="dupla_list",
    ),
    path(
        "equipo-tecnico/exportar/",
        permissions_any_required(["Admin", "Exportar a csv"])(DuplaExportView.as_view()),
        name="dupla_exportar",
    ),
    path(
        "equipo-tecnico/crear/",
        permissions_any_required(["Admin"])(DuplaCreateView.as_view()),
        name="dupla_crear",
    ),
    path(
        "equipo-tecnico/<int:pk>/editar/",
        permissions_any_required(["Admin"])(DuplaUpdateView.as_view()),
        name="dupla_editar",
    ),
    path(
        "equipo-tecnico/<int:pk>/",
        permissions_any_required(["Admin"])(DuplaDetailView.as_view()),
        name="dupla_detalle",
    ),
    path(
        "equipo-tecnico/<int:pk>/eliminar/",
        permissions_any_required(["Admin"])(DuplaDeleteView.as_view()),
        name="dupla_eliminar",
    ),
]
