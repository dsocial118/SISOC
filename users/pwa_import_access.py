"""Resolución de espacios de Comedores requerida por importaciones PWA."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class ComedorOrganizacionPWA:
    """Comedor expandido desde una organización asignada en un import PWA."""

    comedor_id: int
    organizacion_id: int


@dataclass(frozen=True)
class SeleccionAccesosPWAImportacion:
    """IDs y expansiones de dominio necesarios para sincronizar accesos PWA."""

    organizacion_ids: tuple[int, ...] = ()
    comedor_ids: tuple[int, ...] = ()
    comedores_por_organizacion: tuple[ComedorOrganizacionPWA, ...] = ()
    comedor_id_alimentar_comunidad: int | None = None

    @property
    def tiene_asignaciones(self) -> bool:
        return bool(self.organizacion_ids or self.comedor_ids)


ResolverAccesosPWAImportacion = Callable[[str, str], SeleccionAccesosPWAImportacion]
_resolver: ResolverAccesosPWAImportacion | None = None


def registrar_resolvedor_accesos_pwa_importacion(
    resolver: ResolverAccesosPWAImportacion,
) -> None:
    """Registra el proveedor de Comedores para importaciones PWA de Users."""
    global _resolver  # pylint: disable=global-statement

    if _resolver is None or _resolver is resolver:
        _resolver = resolver
        return
    raise ValueError("Ya existe un resolvedor de accesos PWA de importacion.")


def resolver_accesos_pwa_importacion(
    organizaciones_raw: str, comedores_raw: str
) -> SeleccionAccesosPWAImportacion:
    """Valida y expande las asignaciones de Comedores de una fila PWA."""
    if _resolver is None:
        raise RuntimeError(
            "No hay un resolvedor de accesos PWA de importacion registrado."
        )
    return _resolver(organizaciones_raw, comedores_raw)
