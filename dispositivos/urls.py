from django.urls import path
from core.decorators import permissions_any_required
from dispositivos.views import (
    DispositivoCreateView,
    DispositivoUpdateView,
    DispositivoDeleteView,
    DispositivoListView,
    DispositivoDetailView,
)


urlpatterns = [
    path(
        "dispositivos/crear",
        permissions_any_required(["dispositivos.add_dispositivo"])(
            DispositivoCreateView.as_view()
        ),
        name="dispositivos_crear",
    ),
    path(
        "dispositivos/<int:pk>/",
        permissions_any_required(["dispositivos.view_dispositivo"])(
            DispositivoDetailView.as_view()
        ),
        name="dispositivos_detalle",
    ),
    path(
        "dispositivos/<int:pk>/editar",
        permissions_any_required(["dispositivos.change_dispositivo"])(
            DispositivoUpdateView.as_view()
        ),
        name="dispositivos_editar",
    ),
    path(
        "dispositivos/<int:pk>/eliminar",
        permissions_any_required(["dispositivos.delete_dispositivo"])(
            DispositivoDeleteView.as_view()
        ),
        name="dispositivos_eliminar",
    ),
    path(
        "dispositivos/",
        permissions_any_required(["dispositivos.view_dispositivo"])(
            DispositivoListView.as_view()
        ),
        name="dispositivos_listar",
    ),
]
