from django.urls import path
from configuraciones.decorators import group_required
from dupla.views import (
    DuplaCreateView,
    DuplaDeleteView,
    DuplaDetailView,
    DuplaListView,
    DuplaUpdateView,
)

urlpatterns = [
    path(
        "dupla/",
        DuplaListView.as_view(),
        name="dupla_list",
    ),
    path(
        "dupla/crear/",
        DuplaCreateView.as_view(),
        name="dupla_crear",
    ),
    path(
        "dupla/<int:pk>/actualizar/",
        DuplaUpdateView.as_view(),
        name="dupla_actualizar",
    ),
    path(
        "dupla/<int:pk>/",
        DuplaDetailView.as_view(),
        name="dupla_detalle",
    ),
    path(
        "dupla/<int:pk>/eliminar/",
        DuplaDeleteView.as_view(),
        name="dupla_eliminar",
    ),


]