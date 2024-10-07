from django.urls import include, path

from comedores.urls import api_urls, web_urls

urlpatterns = [
    path("", include(api_urls)),
    path("", include(web_urls)),
]
