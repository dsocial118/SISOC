"""Contrato Python público de Celiaquía para consumidores externos."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from celiaquia.models import ExpedienteCiudadano


@dataclass(frozen=True)
class LegajoResumenCiudadano:
    """Datos de Celiaquía aptos para mostrar fuera del dominio."""

    estado_expediente: str
    estado_legajo: str
    resultado_cruce: str
    estado_cupo: str
    es_titular_activo: bool
    revision_tecnica: str
    creado_en: datetime


@dataclass(frozen=True)
class ResumenCiudadano:
    """Resumen de los legajos de un ciudadano dentro de Celiaquía."""

    legajo_actual: LegajoResumenCiudadano | None
    historial: tuple[LegajoResumenCiudadano, ...]


def obtener_resumen_ciudadano(ciudadano_id: int) -> ResumenCiudadano:
    """Devuelve el resumen de Celiaquía del ciudadano sin filtrar ORM."""

    legajos = tuple(
        LegajoResumenCiudadano(
            estado_expediente=legajo.expediente.estado.nombre,
            estado_legajo=legajo.estado.nombre,
            resultado_cruce=legajo.get_resultado_sintys_display(),
            estado_cupo=legajo.get_estado_cupo_display(),
            es_titular_activo=legajo.es_titular_activo,
            revision_tecnica=legajo.get_revision_tecnico_display(),
            creado_en=legajo.creado_en,
        )
        for legajo in (
            ExpedienteCiudadano.objects.filter(ciudadano_id=ciudadano_id)
            .select_related("expediente__estado", "estado")
            .order_by("-creado_en")
        )
    )
    return ResumenCiudadano(
        legajo_actual=legajos[0] if legajos else None,
        historial=legajos,
    )
