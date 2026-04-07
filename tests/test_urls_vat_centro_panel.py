from django.http import HttpResponse
from django.urls import include, path


def _placeholder_view(request, *args, **kwargs):
    return HttpResponse("ok")


urlpatterns = [
    path("", _placeholder_view, name="inicio"),
    path("changelog/", _placeholder_view, name="changelog"),
    path("logout/", _placeholder_view, name="logout"),
    path("", include("VAT.urls")),
]
