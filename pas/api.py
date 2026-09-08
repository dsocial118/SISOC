"""Contrato Python público de PAS para consumidores externos."""

from pas.services.resumen_publico_service import (
    ResumenTitularPAS,
    obtener_resumen_titular as _obtener_resumen_titular,
)

__all__ = ["ResumenTitularPAS", "obtener_resumen_titular"]


def obtener_resumen_titular(persona_id: int) -> ResumenTitularPAS | None:
    """Devuelve el resumen público de un titular PAS, o ``None`` si no existe."""

    return _obtener_resumen_titular(persona_id)
