"""Configuración de filtros combinables para el listado de ciudadanos.

Alcance deliberadamente parcial. Solo se exponen acá los campos "planos", es
decir los que se traducen a un ``Q`` independiente. Quedan afuera:

- ``estado_revision``: no es un filtro de campo sino lógica condicional (mapea a
  ``requiere_revision_manual`` pero solo si ``tipo_registro_identidad`` está en
  un conjunto acotado y si no hay término de búsqueda o el estado fue elegido
  explícitamente). ``AdvancedFilterEngine`` arma un ``Q`` por fila y los combina
  con AND, así que no puede expresar una condición que dependa de otra fila.
- ``tipo_registro_identidad``: es el campo que gobierna esa condicionalidad, así
  que mover uno sin el otro cambiaría resultados en silencio.

Ambos siguen viviendo en el formulario propio del listado hasta que se defina
qué hacer con ellos.

``documento`` se expone solo con ``eq`` a propósito: la búsqueda por prefijo usa
``Ciudadano.documento_prefix_filter``, que arma un OR de rangos para poder usar
el índice numérico. El motor genérico no tiene hoy un punto de extensión para
reemplazar el lookup por campo, y un ``icontains`` sobre esa columna sería un
scan completo en una tabla que ya evita el ``COUNT`` con ``NoCountPaginator``.
"""

from typing import Any, Dict

from ciudadanos.forms import get_cached_provincia_filter_choices

FIELD_MAP: Dict[str, str] = {
    "apellido": "apellido",
    "nombre": "nombre",
    "documento": "documento",
    "identificador_interno": "identificador_interno",
    # Apunta al nombre y no a provincia_id: el motor traduce choice+eq a
    # `__iexact`, que Django no admite sobre una FK ("Unsupported lookup
    # 'iexact' for ForeignKey"). Es el mismo criterio que centro_filter_config.
    "provincia": "provincia__nombre",
}

FIELD_TYPES: Dict[str, str] = {
    "apellido": "text",
    "nombre": "text",
    "documento": "number",
    "identificador_interno": "text",
    "provincia": "choice",
}

TEXT_OPS = ["contains", "ncontains", "eq", "ne", "empty"]
NUM_OPS = ["eq"]
CHOICE_OPS = ["eq", "ne", "empty"]

FILTER_FIELDS = [
    {"name": "apellido", "label": "Apellido", "type": "text"},
    {"name": "nombre", "label": "Nombre", "type": "text"},
    {"name": "documento", "label": "Documento", "type": "number"},
    {
        "name": "identificador_interno",
        "label": "Identificador interno",
        "type": "text",
    },
    {"name": "provincia", "label": "Provincia", "type": "choice"},
]


def _provincias_a_ui():
    """Opciones de provincia por NOMBRE, no por id.

    El filtro apunta a ``provincia__nombre``, asi que el valor enviado tiene que
    ser el nombre. ``get_cached_provincia_filter_choices`` devuelve ``(id, nombre)``
    porque lo usa el formulario propio del listado, que si filtra por FK.
    """

    return [
        {"value": nombre, "label": nombre}
        for _id, nombre in get_cached_provincia_filter_choices()
    ]


def get_filters_ui_config() -> Dict[str, Any]:
    """Configuración serializable para el front de filtros avanzados."""

    fields = [dict(field) for field in FILTER_FIELDS]
    for field in fields:
        if field["name"] == "provincia":
            field["choices"] = _provincias_a_ui()

    return {
        "fields": fields,
        "operators": {
            "text": list(TEXT_OPS),
            "number": list(NUM_OPS),
            "choice": list(CHOICE_OPS),
        },
        "defaultOperators": {
            "text": "contains",
            "number": "eq",
            "choice": "eq",
        },
    }


__all__ = [
    "FIELD_MAP",
    "FIELD_TYPES",
    "TEXT_OPS",
    "NUM_OPS",
    "CHOICE_OPS",
    "FILTER_FIELDS",
    "get_filters_ui_config",
]
