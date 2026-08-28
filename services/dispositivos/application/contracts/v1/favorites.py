"""Contrato v1 para integrar filtros favoritos sin importar Core."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ConfiguracionFavoritos:
    seccion: str
    tipos_campos: dict[str, str]
    operadores_permitidos: dict[str, tuple[str, ...]]
