from django.urls import path

from .runtime import required_permissions
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
        required_permissions(["dispositivos.add_dispositivo"])(
            DispositivoCreateView.as_view()
        ),
        name="dispositivos_crear",
    ),
    path(
        "dispositivos/<int:pk>/",
        required_permissions(["dispositivos.view_dispositivo"])(
            DispositivoDetailView.as_view()
        ),
        name="dispositivos_detalle",
    ),
    path(
        "dispositivos/<int:pk>/editar",
        required_permissions(["dispositivos.change_dispositivo"])(
            DispositivoUpdateView.as_view()
        ),
        name="dispositivos_editar",
    ),
    path(
        "dispositivos/<int:pk>/eliminar",
        required_permissions(["dispositivos.delete_dispositivo"])(
            DispositivoDeleteView.as_view()
        ),
        name="dispositivos_eliminar",
    ),
    path(
        "dispositivos/",
        required_permissions(["dispositivos.view_dispositivo"])(
            DispositivoListView.as_view()
        ),
        name="dispositivos_listar",
    ),
]
