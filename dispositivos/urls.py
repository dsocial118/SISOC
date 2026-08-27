from django.urls import path

from .adapters.monolith_permissions import permisos_requeridos
from .views import (
    DispositivoCreateView,
    DispositivoUpdateView,
    DispositivoDeleteView,
    DispositivoListView,
    DispositivoDetailView,
)


urlpatterns = [
    path(
        "dispositivos/crear",
        permisos_requeridos(["dispositivos.add_dispositivo"])(
            DispositivoCreateView.as_view()
        ),
        name="dispositivos_crear",
    ),
    path(
        "dispositivos/<int:pk>/",
        permisos_requeridos(["dispositivos.view_dispositivo"])(
            DispositivoDetailView.as_view()
        ),
        name="dispositivos_detalle",
    ),
    path(
        "dispositivos/<int:pk>/editar",
        permisos_requeridos(["dispositivos.change_dispositivo"])(
            DispositivoUpdateView.as_view()
        ),
        name="dispositivos_editar",
    ),
    path(
        "dispositivos/<int:pk>/eliminar",
        permisos_requeridos(["dispositivos.delete_dispositivo"])(
            DispositivoDeleteView.as_view()
        ),
        name="dispositivos_eliminar",
    ),
    path(
        "dispositivos/",
        permisos_requeridos(["dispositivos.view_dispositivo"])(
            DispositivoListView.as_view()
        ),
        name="dispositivos_listar",
    ),
]
