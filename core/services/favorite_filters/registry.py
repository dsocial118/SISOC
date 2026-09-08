"""Registro de configuraciones de filtros aportadas por cada app."""

from __future__ import annotations

from core.services.favorite_filters.config import ConfiguracionFiltrosSeccion

_CONFIGURACIONES_POR_SECCION: dict[str, ConfiguracionFiltrosSeccion] = {}


def registrar_configuracion_seccion(
    seccion: str,
    configuracion: ConfiguracionFiltrosSeccion,
) -> None:
    """Registra una configuracion de forma idempotente durante el arranque."""
    existente = _CONFIGURACIONES_POR_SECCION.get(seccion)
    if existente is None:
        _CONFIGURACIONES_POR_SECCION[seccion] = configuracion
        return

    if existente != configuracion:
        raise ValueError(
            f"La seccion de filtros favoritos '{seccion}' ya tiene otra configuracion."
        )


def obtener_configuracion_registrada(
    seccion: str,
) -> ConfiguracionFiltrosSeccion | None:
    return _CONFIGURACIONES_POR_SECCION.get(seccion)
