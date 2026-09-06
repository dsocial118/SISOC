"""Lectura del instrumento (cuestionario y catálogos) que publica la app.

Se usa para mostrar las respuestas con etiquetas legibles en el backoffice y
para servir los catálogos a la app. Los archivos son la copia de
`datacalle/instrumento/`; se leen una vez y quedan en memoria.

Regla de oro: las respuestas se guardan como llegan. Si el instrumento local
está desactualizado, se muestra la clave cruda en lugar de perder el dato.
"""

import json
from functools import lru_cache
from pathlib import Path

RUTA = Path(__file__).resolve().parent.parent / "instrumento"


def _leer(nombre):
    archivo = RUTA / nombre
    if not archivo.exists():
        return {}
    try:
        return json.loads(archivo.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


@lru_cache(maxsize=1)
def get_cuestionario() -> dict:
    return _leer("cuestionario.json")


@lru_cache(maxsize=1)
def get_catalogos() -> dict:
    return _leer("catalogos.json")


@lru_cache(maxsize=1)
def get_version() -> str:
    return str(get_cuestionario().get("version") or "")


@lru_cache(maxsize=1)
def _campos_por_id() -> dict:
    """Mapa ``id de campo -> definición``, aplanando las páginas."""
    campos = {}
    for pagina in get_cuestionario().get("paginas", []):
        for campo in pagina.get("campos", []):
            campo_id = campo.get("id")
            if campo_id:
                campos[campo_id] = {**campo, "pagina": pagina.get("titulo", "")}
    return campos


@lru_cache(maxsize=1)
def _etiquetas_por_catalogo() -> dict:
    """Mapa ``catálogo -> {código: etiqueta}``."""
    mapa = {}
    for nombre, definicion in get_catalogos().items():
        if not isinstance(definicion, dict):
            continue
        opciones = definicion.get("opciones") or []
        mapa[nombre] = {
            opcion.get("codigo"): opcion.get("etiqueta")
            for opcion in opciones
            if isinstance(opcion, dict)
        }
    return mapa


def etiqueta_de_codigo(catalogo, codigo):
    """Etiqueta de un código de catálogo; el propio código si no se conoce."""
    if codigo in (None, ""):
        return ""
    return _etiquetas_por_catalogo().get(catalogo, {}).get(str(codigo), str(codigo))


def _valor_legible(campo, valor):
    catalogo = campo.get("catalogo") if campo else None
    if isinstance(valor, list):
        if catalogo:
            return ", ".join(etiqueta_de_codigo(catalogo, item) for item in valor)
        return ", ".join(str(item) for item in valor)
    if isinstance(valor, dict):
        return json.dumps(valor, ensure_ascii=False)
    if isinstance(valor, bool):
        return "Sí" if valor else "No"
    if catalogo:
        return etiqueta_de_codigo(catalogo, valor)
    return str(valor) if valor not in (None, "") else ""


def respuestas_legibles(encuesta):
    """Respuestas del caso agrupadas por página, con etiquetas del instrumento.

    Las claves que el instrumento local no conoce igual se muestran, con su id
    crudo: nunca se oculta un dato que llegó desde la app.
    """
    respuestas = encuesta.respuestas or {}
    campos = _campos_por_id()
    paginas = {}
    for clave, valor in respuestas.items():
        campo = campos.get(clave)
        titulo = campo.get("pagina") if campo else "Otros datos"
        etiqueta = campo.get("etiqueta") if campo else clave
        # La firma es una imagen embebida: no tiene sentido volcarla como texto.
        if campo and campo.get("tipo") == "firma":
            legible = "(firma registrada)" if valor else ""
        else:
            legible = _valor_legible(campo, valor)
        paginas.setdefault(titulo, []).append(
            {"clave": clave, "etiqueta": etiqueta, "valor": legible}
        )
    return [
        {"titulo": titulo, "items": items} for titulo, items in paginas.items() if items
    ]
