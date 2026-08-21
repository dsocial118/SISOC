from django.urls import path
from core.decorators import permissions_any_required
from rendicioncuentasmensual.views import (
    RendicionCuentaMensualGlobalListView,
    RendicionCuentaMensualListView,
    RendicionCuentaMensualDetailView,
    RendicionCuentaMensualDownloadPdfView,
    RendicionCuentaMensualDeleteView,
    RendicionCuentaMensualCreateView,
    RendicionCuentaMensualUpdateView,
    eliminar_archivo,
)

_RENDICION_PERM = ["rendicioncuentasmensual.view_rendicioncuentamensual"]
_RENDICION_STAGE_PERMS = [
    "rendicioncuentasmensual.manage_territorial_stage",
    "rendicioncuentasmensual.manage_auditoria_review_stage",
    "rendicioncuentasmensual.manage_auditoria_stage",
    "rendicioncuentasmensual.manage_regularizacion_stage",
]
_RENDICION_ACCESS_PERMS = _RENDICION_PERM + _RENDICION_STAGE_PERMS

urlpatterns = [
    path(
        "rendicioncuentasmensual/listado/",
        permissions_any_required(_RENDICION_ACCESS_PERMS)(
            RendicionCuentaMensualGlobalListView.as_view()
        ),
        name="rendicioncuentasmensual_global_list",
    ),
    path(
        "rendicioncuentasmensual/<int:comedor_id>/",
        permissions_any_required(_RENDICION_ACCESS_PERMS)(
            RendicionCuentaMensualListView.as_view()
        ),
        name="rendicioncuentasmensual_list",
    ),
    path(
        "rendicioncuentasmensual/detalle/<int:pk>/",
        permissions_any_required(_RENDICION_ACCESS_PERMS)(
            RendicionCuentaMensualDetailView.as_view()
        ),
        name="rendicioncuentasmensual_detail",
    ),
    path(
        "rendicioncuentasmensual/detalle/<int:pk>/descargar-pdf/",
        permissions_any_required(_RENDICION_ACCESS_PERMS)(
            RendicionCuentaMensualDownloadPdfView.as_view()
        ),
        name="rendicioncuentasmensual_download_pdf",
    ),
    path(
        "rendicioncuentasmensual/eliminar/<int:pk>/",
        permissions_any_required(_RENDICION_PERM)(
            RendicionCuentaMensualDeleteView.as_view()
        ),
        name="rendicioncuentasmensual_delete",
    ),
    path(
        "rendicioncuentasmensual/nuevo/<int:comedor_id>/",
        permissions_any_required(_RENDICION_PERM)(
            RendicionCuentaMensualCreateView.as_view()
        ),
        name="rendicioncuentasmensual_create",
    ),
    path(
        "rendicioncuentasmensual/editar/<int:pk>/",
        permissions_any_required(_RENDICION_PERM)(
            RendicionCuentaMensualUpdateView.as_view()
        ),
        name="rendicioncuentasmensual_update",
    ),
    path(
        "eliminar-archivo/<int:archivo_id>/", eliminar_archivo, name="eliminar_archivo"
    ),
]
