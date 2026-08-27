"""Puertos de infraestructura que el dominio de Dispositivos puede necesitar."""

from typing import Protocol


class CatalogoTerritorial(Protocol):
    """Resuelve los objetos territoriales que la UI de Dispositivos presenta."""

    def obtener_provincia(self, source_id: int | None): ...

    def obtener_municipio(self, source_id: int | None): ...

    def provincias_disponibles(self, alcance: dict[int, set[int] | None] | None): ...

    def municipios_disponibles(
        self, provincia, alcance: dict[int, set[int] | None] | None
    ): ...

    def municipios_vacios(self): ...
