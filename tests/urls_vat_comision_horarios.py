from django.http import HttpResponse
from django.urls import include, path


def _ok_view(_request):
    return HttpResponse("ok")


urlpatterns = [
    path("inicio/", _ok_view, name="inicio"),
    path("logout/", _ok_view, name="logout"),
    path("changelog/", _ok_view, name="changelog"),
    path("comunicados/", _ok_view, name="comunicados"),
    path("comunicados/gestion/", _ok_view, name="comunicados_gestion"),
    path("grupos/", _ok_view, name="grupos"),
    path("usuarios/", _ok_view, name="usuarios"),
    path("api/buscar-ciudadanos/", _ok_view, name="api_buscar_ciudadanos"),
    path("", include("VAT.urls")),
]
