from django.contrib import admin
from django.shortcuts import redirect
from django.urls import include, path

from VAT.views.reporte import ReporteInscriptosAsistenciasView


def _root_redirect(_request):
    return redirect("vat_reporte_inscripciones_asistencias")


urlpatterns = [
    path("inicio/", _root_redirect, name="inicio"),
    path("dashboard/", _root_redirect, name="dashboard"),
    path("vat/centros/", _root_redirect, name="vat_centro_list"),
    path("login/", admin.site.login, name="login"),
    path("logout", _root_redirect, name="logout"),
    path("admin/", admin.site.urls),
    path("__debug__/", include("debug_toolbar.urls")),
    path("", _root_redirect),
    path(
        "vat/reportes/inscripciones-asistencias/",
        ReporteInscriptosAsistenciasView.as_view(),
        name="vat_reporte_inscripciones_asistencias",
    ),
]
