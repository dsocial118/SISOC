from django.urls import path
from core.decorators import permissions_any_required
from dispositivos.views import (
    DispositivoCreateView,
    DispositivoUpdateView,
    DispositivoDeleteView,
    DispositivoListView,
)


urlpatterns = [
       path(
        "dispositivos/crear",
        permissions_any_required(["DispositivoCreateView"])(
            DispositivoCreateView.as_view()
        ),
        name="dispositivos_crear",
    ),
    path(
        "dispositivos/<int:pk>/editar",
        permissions_any_required(["DispositivoUpdateView"])(
            DispositivoUpdateView.as_view()
        ),
        name="dispositivos_editar",
    ),
    path(
        "dispositivos/<int:pk>/eliminar",
        permissions_any_required(["DispositivoDeleteView"])(
            DispositivoDeleteView.as_view()
        ),
        name="dispositivos_eliminar",
    ),
    path(
        "dispositivos/",
        permissions_any_required(["DispositivoListView"])(
            DispositivoListView.as_view()
        ),
        name="dispositivos_listar",
    ),
]