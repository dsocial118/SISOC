from django.http import HttpResponse
from django.urls import path

from comedores.api_views import ComedorDetailViewSet
from pwa.api_views import MensajeEspacioPWAViewSet
from users.views import UserListView


def _placeholder_view(request, *args, **kwargs):
    return HttpResponse("ok")


urlpatterns = [
    path("usuarios/", UserListView.as_view(), name="usuarios"),
    path("column-preferences/", _placeholder_view, name="column_preferences"),
    path("usuarios/exportar/", _placeholder_view, name="usuarios_exportar"),
    path("usuarios/crear/", _placeholder_view, name="usuario_crear"),
    path("usuarios/editar/<int:pk>/", _placeholder_view, name="usuario_editar"),
    path("usuarios/borrar/<int:pk>/", _placeholder_view, name="usuario_borrar"),
    path("usuarios/activar/<int:pk>/", _placeholder_view, name="usuario_activar"),
    path(
        "api/pwa/espacios/<int:comedor_id>/mensajes/",
        MensajeEspacioPWAViewSet.as_view({"get": "list"}),
    ),
    path(
        "api/comedores/<int:pk>/documentos/",
        ComedorDetailViewSet.as_view({"get": "documentos"}),
    ),
]
