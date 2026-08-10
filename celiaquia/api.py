"""Contrato Python público de Celiaquía para consumidores externos."""

from __future__ import annotations

from celiaquia.services.ciudadano_resumen_service import (
    LegajoResumenCiudadano,
    ResumenCiudadano,
    obtener_resumen_ciudadano as _obtener_resumen_ciudadano,
)


def obtener_resumen_ciudadano(ciudadano_id: int) -> ResumenCiudadano:
    """Devuelve el resumen público de Celiaquía del ciudadano."""

    return _obtener_resumen_ciudadano(ciudadano_id)
