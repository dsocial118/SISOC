from django.urls import path
from provincias.views.web_views import (
    ProyectoCreateView,
    ProyectoListView,
    ProyectoUpdateView,
    ProyectoDeleteView,
    AnexoSocioProductivoCreateView,
)

urlpatterns = [
    path("proyectos/", ProyectoListView.as_view(), name="proyecto_list"),
    path("proyectos/create/", ProyectoCreateView.as_view(), name="proyecto_create"),
    path(
        "proyectos/<int:pk>/update/",
        ProyectoUpdateView.as_view(),
        name="proyecto_update",
    ),
    path(
        "proyectos/<int:pk>/delete/",
        ProyectoDeleteView.as_view(),
        name="proyecto_delete",
    ),
    path(
        "socio_productivo/create/",
        ProyectoCreateView.as_view(),
        name="socio_productivo_create",
    ),
    path("formacion/create/", ProyectoCreateView.as_view(), name="formacion_create"),
    path(
        "anexos/nuevo/", AnexoSocioProductivoCreateView.as_view(), name="anexo_create"
    ),
]
