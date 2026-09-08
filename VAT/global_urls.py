"""Rutas globales de VAT que puede incluir la composición del proyecto."""

from django.urls import path

from VAT.views.reporte import ReporteInscriptosAsistenciasView


urlpatterns = [
    path(
        "vat/reportes/inscripciones-asistencias/",
        ReporteInscriptosAsistenciasView.as_view(),
        name="vat_reporte_inscripciones_asistencias",
    ),
]
