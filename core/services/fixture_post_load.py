"""Callbacks de dominio posteriores a la carga de fixtures."""

from __future__ import annotations

from collections.abc import Callable


FixturePostLoadHandler = Callable[[], str]
_HANDLERS: dict[str, FixturePostLoadHandler] = {}


def registrar_fixture_post_load_handler(
    nombre: str, handler: FixturePostLoadHandler
) -> None:
    """Registra un callback idempotente para el comando ``load_fixtures``."""
    existente = _HANDLERS.get(nombre)
    if existente is None or existente is handler:
        _HANDLERS[nombre] = handler
        return
    raise ValueError(f"Ya existe un callback post-fixture registrado para '{nombre}'.")


def ejecutar_fixture_post_load_handlers() -> tuple[str, ...]:
    """Ejecuta callbacks por nombre para no depender del orden de arranque."""
    return tuple(_HANDLERS[nombre]() for nombre in sorted(_HANDLERS))
