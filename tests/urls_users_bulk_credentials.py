from django.http import HttpResponse
from django.urls import include, path


def _ok_view(_request):
    return HttpResponse("ok")


urlpatterns = [
    path("inicio/", _ok_view, name="inicio"),
    path("", include("users.urls")),
]
