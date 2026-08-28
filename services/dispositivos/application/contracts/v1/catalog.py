"""Contrato v1 del catálogo territorial consumido por Dispositivos."""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ProvinciaCatalogo:
    source_id: int
    nombre: str


@dataclass(frozen=True)
class MunicipioCatalogo:
    source_id: int
    provincia_source_id: int
    nombre: str


@dataclass(frozen=True)
class SnapshotCatalogoTerritorial:
    version: str
    provincias: tuple[ProvinciaCatalogo, ...]
    municipios: tuple[MunicipioCatalogo, ...]


class CatalogoTerritorialV1(Protocol):
    """Publica snapshots completos, sin filtrar modelos ORM del proveedor."""

    def obtener_snapshot(self) -> SnapshotCatalogoTerritorial: ...
