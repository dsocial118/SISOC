from django.urls import include, path


urlpatterns = [
    path("api/comedores/", include("comedores.api_urls")),
]
