from django.urls import path

from configuraciones.decorators import group_required
from organizaciones.views import (
    OrganizacionListView,
    OrganizacionCreateView,
    OrganizacionUpdateView,
    OrganizacionDetailView,
    OrganizacionDeleteView,
)

urlpatterns = [
    path(
        "organizaciones/listar",
        group_required("Organizaciones")(OrganizacionListView.as_view()),
        name="organizaciones",
    ),
    path(
        "organizaciones/crear",
        group_required("Organizaciones")(OrganizacionCreateView.as_view()),
        name="organizacion_crear",
    ),
    path(
        "organizaciones/editar/<int:pk>",
        group_required("Organizaciones")(OrganizacionUpdateView.as_view()),
        name="organizacion_editar",
    ),
    path(
        "organizaciones/detalle/<int:pk>",
        group_required("Organizaciones")(OrganizacionDetailView.as_view()),
        name="organizacion_detalle",
    ),
    path(
        "organizaciones/eliminar/<int:pk>",
        group_required("Organizaciones")(OrganizacionDeleteView.as_view()),
        name="organizacion_eliminar",
    ),
]
