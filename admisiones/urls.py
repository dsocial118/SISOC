from django.urls import include, path

from admisiones.urls import web_urls

urlpatterns = [
    path("", include(web_urls)),
]
