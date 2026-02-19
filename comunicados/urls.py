from django.urls import path
from . import views

urlpatterns = [
    # Vista pública (todos los usuarios)
    path(
        "comunicados/",
        views.ComunicadoListView.as_view(),
        name="comunicados",
    ),
    # Vista de gestión (usuarios con permisos)
    path(
        "comunicados/gestion/",
        views.ComunicadoGestionListView.as_view(),
        name="comunicados_gestion",
    ),
    # CRUD
    path(
        "comunicados/crear/",
        views.ComunicadoCreateView.as_view(),
        name="comunicados_crear",
    ),
    path(
        "comunicados/ver/<int:pk>/",
        views.ComunicadoDetailView.as_view(),
        name="comunicados_ver",
    ),
    path(
        "comunicados/editar/<int:pk>/",
        views.ComunicadoUpdateView.as_view(),
        name="comunicados_editar",
    ),
    path(
        "comunicados/eliminar/<int:pk>/",
        views.ComunicadoDeleteView.as_view(),
        name="comunicados_eliminar",
    ),
    # Acciones
    path(
        "comunicados/publicar/<int:pk>/",
        views.ComunicadoPublicarView.as_view(),
        name="comunicados_publicar",
    ),
    path(
        "comunicados/archivar/<int:pk>/",
        views.ComunicadoArchivarView.as_view(),
        name="comunicados_archivar",
    ),
    path(
        "comunicados/toggle-destacado/<int:pk>/",
        views.ComunicadoToggleDestacadoView.as_view(),
        name="comunicados_toggle_destacado",
    ),
]
