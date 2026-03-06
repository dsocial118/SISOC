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
        permissions_any_required(["auth.role_admin"])(DuplaListView.as_view()),
        name="dupla_list",
    ),
    path(
        "equipo-tecnico/exportar/",
        permissions_any_required(["auth.role_admin", "auth.role_exportar_a_csv"])(
            DuplaExportView.as_view()
        ),
        name="dupla_exportar",
    ),
    path(
        "equipo-tecnico/crear/",
        permissions_any_required(["auth.role_admin"])(DuplaCreateView.as_view()),
        name="dupla_crear",
    ),
    path(
        "equipo-tecnico/<int:pk>/editar/",
        permissions_any_required(["auth.role_admin"])(DuplaUpdateView.as_view()),
        name="dupla_editar",
    ),
    path(
        "equipo-tecnico/<int:pk>/",
        permissions_any_required(["auth.role_admin"])(DuplaDetailView.as_view()),
        name="dupla_detalle",
    ),
    path(
        "equipo-tecnico/<int:pk>/eliminar/",
        permissions_any_required(["auth.role_admin"])(DuplaDeleteView.as_view()),
        name="dupla_eliminar",
    ),
]
