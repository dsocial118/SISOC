from django.urls import include, path

urlpatterns = [
    path("", include("admisiones2.urls.web_urls")),
]
