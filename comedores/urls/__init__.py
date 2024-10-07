from comedores.urls.api_urls import urlpatterns as api_urlpatterns
from comedores.urls.web_urls import urlpatterns as web_urlpatterns

urlpatterns = api_urlpatterns + web_urlpatterns
