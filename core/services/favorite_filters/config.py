"""Contrato compartido para configuraciones de filtros favoritos."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

TTL_CACHE_FILTROS_FAVORITOS = 300


class SeccionesFiltrosFavoritos:
    """Identificadores estables de secciones para filtros favoritos."""

    COMEDORES = "comedores"
    USUARIOS = "usuarios"
    ADMISIONES_TECNICOS = "admisiones_tecnicos"
    ADMISIONES_LEGALES = "admisiones_legales"
    DUPLAS = "duplas"
    CDF_CENTROS = "centrodefamilia_centros"
    CDF_BENEFICIARIOS = "centrodefamilia_beneficiarios"
    CDF_RESPONSABLES = "centrodefamilia_responsables"
    VAT_CENTROS = "vat_centros"
    DISPOSITIVOS = "dispositivos"
    RENDICIONES = "rendiciones"


@dataclass(frozen=True)
class ConfiguracionFiltrosSeccion:
    tipos_campos: Mapping[str, str]
    operadores_permitidos: Mapping[str, Iterable[str]]


def clave_cache_filtros_favoritos(id_usuario: int, seccion: str) -> str:
    return f"filtros_favoritos_{id_usuario}_{seccion}"


def obtener_configuracion_seccion(
    seccion: str,
) -> ConfiguracionFiltrosSeccion | None:
    """Obtiene la configuracion aportada por la app dueña de la seccion."""
    from core.services.favorite_filters.registry import (  # pylint: disable=import-outside-toplevel
        obtener_configuracion_registrada,
    )

    return obtener_configuracion_registrada(seccion)
