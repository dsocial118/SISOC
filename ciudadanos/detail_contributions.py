"""Registro de contextos aportados por dominios a Ciudadano 360."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

ContribucionDetalleCiudadano = Callable[[Any, Any], dict[str, Any]]

_CONTRIBUCIONES: dict[str, ContribucionDetalleCiudadano] = {}


def registrar_contribucion_detalle(
    nombre: str,
    contribucion: ContribucionDetalleCiudadano,
) -> None:
    """Registra una contribucion determinista e idempotente."""
    existente = _CONTRIBUCIONES.get(nombre)
    if existente is None or existente is contribucion:
        _CONTRIBUCIONES[nombre] = contribucion
        return
    raise ValueError(f"La contribucion de Ciudadano 360 '{nombre}' ya existe.")


def obtener_contexto_contribucion(
    nombre: str,
    ciudadano: Any,
    logger: Any,
    fallback: Callable[[], dict[str, Any]],
) -> dict[str, Any]:
    """Resuelve una contribucion registrada sin importar su implementacion."""
    contribucion = _CONTRIBUCIONES.get(nombre)
    return contribucion(ciudadano, logger) if contribucion else fallback()
