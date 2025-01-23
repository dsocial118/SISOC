from django.urls import path
from django.contrib.auth.decorators import login_required

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
        login_required(OrganizacionListView.as_view()),
        name="organizaciones",
    ),
    path(
        "organizaciones/crear",
        login_required(OrganizacionCreateView.as_view()),
        name="organizacion_crear",
    ),
    path(
        "organizaciones/editar/<int:pk>",
        login_required(OrganizacionUpdateView.as_view()),
        name="organizacion_editar",
    ),
    path(
        "organizaciones/detalle/<int:pk>",
        login_required(OrganizacionDetailView.as_view()),
        name="organizacion_detalle",
    ),
    path(
        "organizaciones/eliminar/<int:pk>",
        login_required(OrganizacionDeleteView.as_view()),
        name="organizacion_eliminar",
    ),
]
