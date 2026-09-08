"""Registro de restricciones de navegacion aportadas por dominios."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

SidebarAccessPredicate = Callable[[Any], bool]

_PREDICADOS: dict[str, SidebarAccessPredicate] = {}


def registrar_predicado_sidebar(nombre: str, predicado: SidebarAccessPredicate) -> None:
    """Registra un predicado de forma idempotente durante el arranque."""
    existente = _PREDICADOS.get(nombre)
    if existente is None or existente is predicado:
        _PREDICADOS[nombre] = predicado
        return
    raise ValueError(f"El predicado de sidebar '{nombre}' ya existe.")


def resolver_predicado_sidebar(nombre: str, user: Any) -> bool:
    predicado = _PREDICADOS.get(nombre)
    return bool(predicado(user)) if predicado else False
