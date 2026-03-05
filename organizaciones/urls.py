from django.urls import path

from core.decorators import permissions_any_required
from organizaciones.views import (
    OrganizacionListView,
    OrganizacionCreateView,
    OrganizacionUpdateView,
    OrganizacionDetailView,
    OrganizacionDeleteView,
    FirmanteCreateView,
    AvalCreateView,
    AvalUpdateView,
    FirmanteUpdateView,
    FirmanteDeleteView,
    AvalDeleteView,
    sub_tipo_entidad_ajax,
    organizaciones_ajax,
)
from organizaciones.views_export import OrganizacionExportView


urlpatterns = [
    path(
        "organizaciones/listar",
        permissions_any_required(["Organizaciones"])(OrganizacionListView.as_view()),
        name="organizaciones",
    ),
    path(
        "organizaciones/exportar",
        permissions_any_required(["Organizaciones", "Exportar a csv"])(
            OrganizacionExportView.as_view()
        ),
        name="organizacion_exportar",
    ),
    path(
        "organizaciones/crear",
        permissions_any_required(["Organizaciones"])(OrganizacionCreateView.as_view()),
        name="organizacion_crear",
    ),
    path(
        "organizaciones/editar/<int:pk>",
        permissions_any_required(["Organizaciones"])(OrganizacionUpdateView.as_view()),
        name="organizacion_editar",
    ),
    path(
        "organizaciones/detalle/<int:pk>",
        permissions_any_required(["Organizaciones"])(OrganizacionDetailView.as_view()),
        name="organizacion_detalle",
    ),
    path(
        "organizaciones/eliminar/<int:pk>",
        permissions_any_required(["Organizaciones"])(OrganizacionDeleteView.as_view()),
        name="organizacion_eliminar",
    ),
    path(
        "organizaciones/firmante/crear/<int:organizacion_pk>",
        permissions_any_required(["Organizaciones"])(FirmanteCreateView.as_view()),
        name="firmante_crear",
    ),
    path(
        "organizaciones/firmante/editar/<int:pk>",
        permissions_any_required(["Organizaciones"])(FirmanteUpdateView.as_view()),
        name="firmante_editar",
    ),
    path(
        "organizaciones/firmante/eliminar/<int:pk>",
        permissions_any_required(["Organizaciones"])(FirmanteDeleteView.as_view()),
        name="firmante_eliminar",
    ),
    path(
        "organizaciones/aval/crear/<int:organizacion_pk>",
        permissions_any_required(["Organizaciones"])(AvalCreateView.as_view()),
        name="aval_crear",
    ),
    path(
        "organizaciones/aval/editar/<int:pk>",
        permissions_any_required(["Organizaciones"])(AvalUpdateView.as_view()),
        name="aval_editar",
    ),
    path(
        "organizaciones/aval/eliminar/<int:pk>",
        permissions_any_required(["Organizaciones"])(AvalDeleteView.as_view()),
        name="aval_eliminar",
    ),
    path(
        "organizaciones/subtipos-entidad/ajax/",
        permissions_any_required(["Organizaciones"])(sub_tipo_entidad_ajax),
        name="organizacion_subtipos_entidad_ajax",
    ),
    path(
        "organizaciones/ajax/",
        permissions_any_required(["Organizaciones"])(organizaciones_ajax),
        name="organizaciones_ajax",
    ),
]
