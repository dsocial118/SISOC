"""Puerto compartido para consultas RENAPER."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

ConsultaRenaper = Callable[[str, str], dict[str, Any]]

_consultar_datos_renaper: ConsultaRenaper | None = None


def registrar_consulta_renaper(consulta: ConsultaRenaper) -> None:
    """Registra el proveedor tecnico una vez, sin consultar la base."""
    global _consultar_datos_renaper

    if _consultar_datos_renaper is None or _consultar_datos_renaper is consulta:
        _consultar_datos_renaper = consulta
        return
    raise ValueError("Ya existe un proveedor RENAPER registrado.")


def consultar_datos_renaper(dni: str, sexo: str) -> dict[str, Any]:
    """Consulta RENAPER mediante el proveedor registrado por un dominio."""
    if _consultar_datos_renaper is None:
        raise RuntimeError("No hay un proveedor RENAPER registrado.")
    return _consultar_datos_renaper(dni, sexo)
