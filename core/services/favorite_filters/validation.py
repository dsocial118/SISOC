"""Validaciones de payloads para filtros favoritos."""

from __future__ import annotations

import json
from typing import Any, Mapping, Optional

from .config import ConfiguracionFiltrosSeccion


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
