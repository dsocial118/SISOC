from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.urls import include, path
from django.views.generic import TemplateView

from .views import *

urlpatterns = [
    path(
        "metricas/",
        login_required(TemplateView.as_view(template_name="metricas.html")),
        name="metricas",
    ),
    path("busqueda/menu", login_required(BusquedaMenu.as_view()), name="busqueda_menu"),
    # Django Debug Toolbar
    path("__debug__/", include("debug_toolbar.urls")),
]
