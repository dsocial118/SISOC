"""Rutas globales cuyo dominio funcional pertenece a Celiaquía."""

from django.urls import path

from celiaquia.views.reporter_provincias import ReporterProvinciasView
from core.decorators import permissions_any_required


urlpatterns = [
    path(
        "reporter-provincias/",
        permissions_any_required(["celiaquia.view_reporte_provincias"])(
            ReporterProvinciasView.as_view()
        ),
        name="reporter_provincias",
    ),
]
