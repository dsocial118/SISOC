from django.urls import include, path


urlpatterns = [
    path("", include("services.dispositivos.dispositivos.urls")),
]
