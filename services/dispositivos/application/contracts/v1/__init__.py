"""Contratos públicos versionados del núcleo de Dispositivos."""

from .catalog import (
    CatalogoTerritorialV1,
    MunicipioCatalogo,
    ProvinciaCatalogo,
    SnapshotCatalogoTerritorial,
)
from .favorites import ConfiguracionFavoritos
from .identity import DispositivosActor, TerritorialScope, get_geography_scope_map

__all__ = [
    "CatalogoTerritorialV1",
    "ConfiguracionFavoritos",
    "DispositivosActor",
    "MunicipioCatalogo",
    "ProvinciaCatalogo",
    "SnapshotCatalogoTerritorial",
    "TerritorialScope",
    "get_geography_scope_map",
]
