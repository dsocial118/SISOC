from django.urls import include, path

urlpatterns = [path("", include("pwa.api_urls"))]
