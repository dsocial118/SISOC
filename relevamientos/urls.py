from django.urls import include, path

from relevamientos.urls import web_urls
from relevamientos.urls import api_urls

urlpatterns = [
    path("", include(api_urls)),
    path("", include(web_urls)),
]
