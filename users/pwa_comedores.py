"""Capacidades de Comedores requeridas por los accesos PWA."""

from __future__ import annotations

from collections.abc import Callable


EsAlimentarComunidad = Callable[[int], bool]
_es_alimentar_comunidad: EsAlimentarComunidad | None = None


def registrar_capacidad_alimentar_comunidad(capacidad: EsAlimentarComunidad) -> None:
    """Registra la regla de programa provista por Comedores."""
    global _es_alimentar_comunidad

    if _es_alimentar_comunidad is None or _es_alimentar_comunidad is capacidad:
        _es_alimentar_comunidad = capacidad
        return
    raise ValueError("Ya existe una capacidad Alimentar Comunidad registrada.")


def es_comedor_alimentar_comunidad(comedor_id: int | None) -> bool:
    """Indica si el comedor debe restringir permisos móviles de rendición."""
    if not comedor_id:
        return False
    if _es_alimentar_comunidad is None:
        raise RuntimeError("No hay una capacidad de Comedores registrada.")
    return bool(_es_alimentar_comunidad(comedor_id))
