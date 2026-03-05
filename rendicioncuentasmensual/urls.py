from django.urls import path
from core.decorators import permissions_any_required
from rendicioncuentasmensual.views import (
    RendicionCuentaMensualListView,
    RendicionCuentaMensualDetailView,
    RendicionCuentaMensualDeleteView,
    RendicionCuentaMensualCreateView,
    RendicionCuentaMensualUpdateView,
    eliminar_archivo,
)

urlpatterns = [
    path(
        "rendicioncuentasmensual/<int:comedor_id>/",
        permissions_any_required(["Tecnico Comedor"])(RendicionCuentaMensualListView.as_view()),
        name="rendicioncuentasmensual_list",
    ),
    path(
        "rendicioncuentasmensual/detalle/<int:pk>/",
        permissions_any_required(["Tecnico Comedor"])(RendicionCuentaMensualDetailView.as_view()),
        name="rendicioncuentasmensual_detail",
    ),
    path(
        "rendicioncuentasmensual/eliminar/<int:pk>/",
        permissions_any_required(["Tecnico Comedor"])(RendicionCuentaMensualDeleteView.as_view()),
        name="rendicioncuentasmensual_delete",
    ),
    path(
        "rendicioncuentasmensual/nuevo/<int:comedor_id>/",
        permissions_any_required(["Tecnico Comedor"])(RendicionCuentaMensualCreateView.as_view()),
        name="rendicioncuentasmensual_create",
    ),
    path(
        "rendicioncuentasmensual/editar/<int:pk>/",
        permissions_any_required(["Tecnico Comedor"])(RendicionCuentaMensualUpdateView.as_view()),
        name="rendicioncuentasmensual_update",
    ),
    path(
        "eliminar-archivo/<int:archivo_id>/", eliminar_archivo, name="eliminar_archivo"
    ),
]
