from django.urls import include, path

urlpatterns = [
    path("", include("admisiones.urls.web_urls")),
]
