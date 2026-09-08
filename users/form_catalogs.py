"""Querysets de dominio requeridos por formularios administrativos de Users."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


QuerysetProvider = Callable[[], Any]
_providers: dict[str, QuerysetProvider] = {}


def registrar_queryset_formulario(nombre: str, provider: QuerysetProvider) -> None:
    """Registra un queryset de dominio para los formularios de Users."""
    existente = _providers.get(nombre)
    if existente is None or existente is provider:
        _providers[nombre] = provider
        return
    raise ValueError(f"Ya existe un queryset de formulario registrado para '{nombre}'.")


def obtener_queryset_formulario(nombre: str) -> Any:
    """Obtiene un queryset aportado por el dominio dueño de sus datos."""
    provider = _providers.get(nombre)
    if provider is None:
        raise RuntimeError(
            f"No hay un queryset de formulario registrado para '{nombre}'."
        )
    return provider()
