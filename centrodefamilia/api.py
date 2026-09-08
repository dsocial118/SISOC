"""Contrato Python público de Centro de Familia."""

from __future__ import annotations

from dataclasses import dataclass

from centrodefamilia.models import ActividadCentro, Centro, ParticipanteActividad


@dataclass(frozen=True)
class MetricasDashboardCentroFamilia:
    """Indicadores agregados que otros módulos pueden mostrar."""

    participantes_total: int
    centros_adheridos_totales: int
    centros_faro_totales: int
    actividades_totales: int


def obtener_metricas_dashboard() -> MetricasDashboardCentroFamilia:
    """Devuelve los indicadores públicos de Centro de Familia para Dashboard."""

    return MetricasDashboardCentroFamilia(
        participantes_total=ParticipanteActividad.objects.filter(
            estado="inscrito"
        ).count(),
        centros_adheridos_totales=Centro.objects.filter(tipo="adherido").count(),
        centros_faro_totales=Centro.objects.filter(tipo="faro").count(),
        actividades_totales=ActividadCentro.objects.count(),
    )
