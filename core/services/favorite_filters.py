"""Utilidades para filtros avanzados favoritos."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Optional

from admisiones.services.admisiones_filter_config import (
    CHOICE_OPS as ADMISIONES_TECNICOS_OPS_ELECCION,
    DATE_OPS as ADMISIONES_TECNICOS_OPS_FECHA,
    FIELD_TYPES as ADMISIONES_TECNICOS_TIPOS_CAMPOS,
    NUM_OPS as ADMISIONES_TECNICOS_OPS_NUMERO,
    TEXT_OPS as ADMISIONES_TECNICOS_OPS_TEXTO,
)
from admisiones.services.legales_filter_config import (
    CHOICE_OPS as ADMISIONES_LEGALES_OPS_ELECCION,
    DATE_OPS as ADMISIONES_LEGALES_OPS_FECHA,
    FIELD_TYPES as ADMISIONES_LEGALES_TIPOS_CAMPOS,
    NUM_OPS as ADMISIONES_LEGALES_OPS_NUMERO,
    TEXT_OPS as ADMISIONES_LEGALES_OPS_TEXTO,
)
from centrodefamilia.services.beneficiarios_filter_config import (
    CHOICE_OPS as BENEFICIARIOS_OPS_ELECCION,
    FIELD_TYPES as BENEFICIARIOS_TIPOS_CAMPOS,
    NUM_OPS as BENEFICIARIOS_OPS_NUMERO,
    TEXT_OPS as BENEFICIARIOS_OPS_TEXTO,
)
from centrodefamilia.services.centro_filter_config import (
    BOOL_OPS as CDF_CENTROS_OPS_BOOLEANO,
    FIELD_TYPES as CDF_CENTROS_TIPOS_CAMPOS,
    NUM_OPS as CDF_CENTROS_OPS_NUMERO,
    TEXT_OPS as CDF_CENTROS_OPS_TEXTO,
)
from centrodefamilia.services.responsables_filter_config import (
    CHOICE_OPS as RESPONSABLES_OPS_ELECCION,
    FIELD_TYPES as RESPONSABLES_TIPOS_CAMPOS,
    NUM_OPS as RESPONSABLES_OPS_NUMERO,
    TEXT_OPS as RESPONSABLES_OPS_TEXTO,
)
from comedores.services.filter_config import (
    CHOICE_OPS as COMEDORES_OPS_ELECCION,
    FIELD_TYPES as COMEDORES_TIPOS_CAMPOS,
    NUM_OPS as COMEDORES_OPS_NUMERO,
    TEXT_OPS as COMEDORES_OPS_TEXTO,
)
from duplas.dupla_filter_config import (
    FIELD_TYPES as DUPLAS_TIPOS_CAMPOS,
    NUM_OPS as DUPLAS_OPS_NUMERO,
    TEXT_OPS as DUPLAS_OPS_TEXTO,
)
from users.users_filter_config import (
    FIELD_TYPES as USUARIOS_TIPOS_CAMPOS,
    NUM_OPS as USUARIOS_OPS_NUMERO,
    TEXT_OPS as USUARIOS_OPS_TEXTO,
)

TTL_CACHE_FILTROS_FAVORITOS = 300


class SeccionesFiltrosFavoritos:
    """Identificadores de secciones para filtros favoritos."""

    COMEDORES = "comedores"
    USUARIOS = "usuarios"
    ADMISIONES_TECNICOS = "admisiones_tecnicos"
    ADMISIONES_LEGALES = "admisiones_legales"
    DUPLAS = "duplas"
    CDF_CENTROS = "centrodefamilia_centros"
    CDF_BENEFICIARIOS = "centrodefamilia_beneficiarios"
    CDF_RESPONSABLES = "centrodefamilia_responsables"


@dataclass(frozen=True)
class ConfiguracionFiltrosSeccion:
    tipos_campos: Mapping[str, str]
    operadores_permitidos: Mapping[str, Iterable[str]]


CONFIGURACIONES_POR_SECCION = {
    SeccionesFiltrosFavoritos.COMEDORES: ConfiguracionFiltrosSeccion(
        tipos_campos=COMEDORES_TIPOS_CAMPOS,
        operadores_permitidos={
            "text": COMEDORES_OPS_TEXTO,
            "number": COMEDORES_OPS_NUMERO,
            "choice": COMEDORES_OPS_ELECCION,
        },
    ),
    SeccionesFiltrosFavoritos.USUARIOS: ConfiguracionFiltrosSeccion(
        tipos_campos=USUARIOS_TIPOS_CAMPOS,
        operadores_permitidos={
            "text": USUARIOS_OPS_TEXTO,
            "number": USUARIOS_OPS_NUMERO,
        },
    ),
    SeccionesFiltrosFavoritos.ADMISIONES_TECNICOS: ConfiguracionFiltrosSeccion(
        tipos_campos=ADMISIONES_TECNICOS_TIPOS_CAMPOS,
        operadores_permitidos={
            "text": ADMISIONES_TECNICOS_OPS_TEXTO,
            "number": ADMISIONES_TECNICOS_OPS_NUMERO,
            "date": ADMISIONES_TECNICOS_OPS_FECHA,
            "choice": ADMISIONES_TECNICOS_OPS_ELECCION,
        },
    ),
    SeccionesFiltrosFavoritos.ADMISIONES_LEGALES: ConfiguracionFiltrosSeccion(
        tipos_campos=ADMISIONES_LEGALES_TIPOS_CAMPOS,
        operadores_permitidos={
            "text": ADMISIONES_LEGALES_OPS_TEXTO,
            "number": ADMISIONES_LEGALES_OPS_NUMERO,
            "date": ADMISIONES_LEGALES_OPS_FECHA,
            "choice": ADMISIONES_LEGALES_OPS_ELECCION,
        },
    ),
    SeccionesFiltrosFavoritos.DUPLAS: ConfiguracionFiltrosSeccion(
        tipos_campos=DUPLAS_TIPOS_CAMPOS,
        operadores_permitidos={
            "text": DUPLAS_OPS_TEXTO,
            "number": DUPLAS_OPS_NUMERO,
        },
    ),
    SeccionesFiltrosFavoritos.CDF_CENTROS: ConfiguracionFiltrosSeccion(
        tipos_campos=CDF_CENTROS_TIPOS_CAMPOS,
        operadores_permitidos={
            "text": CDF_CENTROS_OPS_TEXTO,
            "number": CDF_CENTROS_OPS_NUMERO,
            "boolean": CDF_CENTROS_OPS_BOOLEANO,
        },
    ),
    SeccionesFiltrosFavoritos.CDF_BENEFICIARIOS: ConfiguracionFiltrosSeccion(
        tipos_campos=BENEFICIARIOS_TIPOS_CAMPOS,
        operadores_permitidos={
            "text": BENEFICIARIOS_OPS_TEXTO,
            "number": BENEFICIARIOS_OPS_NUMERO,
            "choice": BENEFICIARIOS_OPS_ELECCION,
        },
    ),
    SeccionesFiltrosFavoritos.CDF_RESPONSABLES: ConfiguracionFiltrosSeccion(
        tipos_campos=RESPONSABLES_TIPOS_CAMPOS,
        operadores_permitidos={
            "text": RESPONSABLES_OPS_TEXTO,
            "number": RESPONSABLES_OPS_NUMERO,
            "choice": RESPONSABLES_OPS_ELECCION,
        },
    ),
}


def clave_cache_filtros_favoritos(id_usuario: int, seccion: str) -> str:
    return f"filtros_favoritos_{id_usuario}_{seccion}"


def obtener_configuracion_seccion(
    seccion: str,
) -> Optional[ConfiguracionFiltrosSeccion]:
    return CONFIGURACIONES_POR_SECCION.get(seccion)


def normalizar_carga(carga: Any) -> Optional[dict[str, Any]]:
    if carga is None:
        return None

    if isinstance(carga, str):
        try:
            carga = json.loads(carga)
        except json.JSONDecodeError:
            return None

    if not isinstance(carga, Mapping):
        return None

    elementos = carga.get("items")
    if elementos is None:
        elementos = []
    if not isinstance(elementos, list):
        return None

    logica = str(carga.get("logic") or "AND").upper()
    if logica not in ("AND", "OR"):
        logica = "AND"

    return {"logic": logica, "items": elementos}


def obtener_items_obsoletos(
    carga: Mapping[str, Any], configuracion: ConfiguracionFiltrosSeccion
) -> list[dict[str, Any]]:
    obsoletos: list[dict[str, Any]] = []
    elementos = carga.get("items") or []
    if not isinstance(elementos, list):
        return [{"motivo": "elementos"}]

    for indice, elemento in enumerate(elementos):
        if not isinstance(elemento, Mapping):
            obsoletos.append({"indice": indice, "motivo": "elemento"})
            continue

        campo = elemento.get("field")
        operador = elemento.get("op")
        if not campo or campo not in configuracion.tipos_campos:
            obsoletos.append({"indice": indice, "motivo": "campo"})
            continue
        if not operador:
            obsoletos.append({"indice": indice, "motivo": "operador"})
            continue

        tipo_campo = configuracion.tipos_campos.get(campo)
        ops_permitidos = configuracion.operadores_permitidos.get(tipo_campo)
        if ops_permitidos is not None and operador not in ops_permitidos:
            obsoletos.append({"indice": indice, "motivo": "operador"})
            continue

        if operador != "empty":
            valor = elemento.get("value")
            if valor is None or (isinstance(valor, str) and valor.strip() == ""):
                obsoletos.append({"indice": indice, "motivo": "valor"})

    return obsoletos


__all__ = [
    "ConfiguracionFiltrosSeccion",
    "SeccionesFiltrosFavoritos",
    "TTL_CACHE_FILTROS_FAVORITOS",
    "clave_cache_filtros_favoritos",
    "normalizar_carga",
    "obtener_configuracion_seccion",
    "obtener_items_obsoletos",
]
