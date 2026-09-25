"""Busqueda de destinatarios para el armado de comunicados (issue #2505).

Reutiliza los motores de filtros combinables de los listados de comedores y
organizaciones, acotando siempre el universo al alcance del usuario.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Tuple

from comedores.models import Comedor
from comedores.services.comedor_service.impl import COMEDOR_ADVANCED_FILTER
from comedores.services.filter_config import (
    get_filters_ui_config as get_comedores_filters_ui_config,
)
from organizaciones.filter_config import (
    ORGANIZACION_ADVANCED_FILTER,
    get_filters_ui_config as get_organizaciones_filters_ui_config,
)
from organizaciones.models import Organizacion

from .permissions import (
    get_ids_comedores_del_usuario,
    get_ids_organizaciones_del_usuario,
)

# Tope de resultados que se listan por pagina en el panel de destinatarios.
PAGE_SIZE = 25

# Tope duro para "agregar todos los resultados": evita que un filtro vacio
# intente cargar decenas de miles de destinatarios en el formulario.
MAX_SELECCION_MASIVA = 2000


def _paginar(queryset, page: int) -> Tuple[List[Any], int, bool]:
    """Devuelve (items, total, hay_mas) para la pagina pedida."""

    page = max(1, page)
    total = queryset.count()
    inicio = (page - 1) * PAGE_SIZE
    fin = inicio + PAGE_SIZE
    return list(queryset[inicio:fin]), total, fin < total


def _comedores_scoped(user):
    ids = get_ids_comedores_del_usuario(user)
    return (
        Comedor.objects.filter(pk__in=ids)
        .select_related("provincia", "municipio", "localidad", "programa")
        .order_by("nombre", "id")
    )


def _organizaciones_scoped(user):
    ids = get_ids_organizaciones_del_usuario(user)
    return (
        Organizacion.objects.filter(pk__in=ids)
        .select_related("tipo_entidad", "provincia", "municipio", "localidad")
        .order_by("nombre", "id")
    )


def _detalle_comedor(comedor: Comedor) -> str:
    partes = [
        getattr(comedor.provincia, "nombre", None),
        getattr(comedor.municipio, "nombre", None),
        getattr(comedor.localidad, "nombre", None),
    ]
    return " · ".join(parte for parte in partes if parte)


def _detalle_organizacion(organizacion: Organizacion) -> str:
    partes = [
        getattr(organizacion.tipo_entidad, "nombre", None),
        getattr(organizacion.provincia, "nombre", None),
        getattr(organizacion.municipio, "nombre", None),
    ]
    return " · ".join(parte for parte in partes if parte)


def buscar_comedores(request, user, page: int = 1) -> Dict[str, Any]:
    """Comedores del usuario que matchean los filtros recibidos."""

    queryset = COMEDOR_ADVANCED_FILTER.filter_queryset(
        _comedores_scoped(user), request
    ).distinct()
    items, total, hay_mas = _paginar(queryset, page)
    return {
        "results": [
            {
                "id": comedor.pk,
                "nombre": comedor.nombre or f"Comedor {comedor.pk}",
                "detalle": _detalle_comedor(comedor),
            }
            for comedor in items
        ],
        "total": total,
        "has_more": hay_mas,
        "page": max(1, page),
        "max_seleccion_masiva": MAX_SELECCION_MASIVA,
    }


def buscar_organizaciones(request, user, page: int = 1) -> Dict[str, Any]:
    """Organizaciones del usuario que matchean los filtros recibidos."""

    queryset = ORGANIZACION_ADVANCED_FILTER.filter_queryset(
        _organizaciones_scoped(user), request
    ).distinct()
    items, total, hay_mas = _paginar(queryset, page)
    return {
        "results": [
            {
                "id": organizacion.pk,
                "nombre": organizacion.nombre or f"Organizacion {organizacion.pk}",
                "detalle": _detalle_organizacion(organizacion),
            }
            for organizacion in items
        ],
        "total": total,
        "has_more": hay_mas,
        "page": max(1, page),
        "max_seleccion_masiva": MAX_SELECCION_MASIVA,
    }


def _seleccionar_todos(queryset) -> Dict[str, Any]:
    total = queryset.count()
    if total > MAX_SELECCION_MASIVA:
        return {
            "results": [],
            "total": total,
            "truncado": True,
            "max_seleccion_masiva": MAX_SELECCION_MASIVA,
        }
    return {
        "results": [
            {"id": pk, "nombre": nombre or f"#{pk}"}
            for pk, nombre in queryset.values_list("pk", "nombre")
        ],
        "total": total,
        "truncado": False,
        "max_seleccion_masiva": MAX_SELECCION_MASIVA,
    }


def seleccionar_todos_comedores(request, user) -> Dict[str, Any]:
    """Todos los comedores que matchean, para el boton 'agregar todos'."""

    return _seleccionar_todos(
        COMEDOR_ADVANCED_FILTER.filter_queryset(
            _comedores_scoped(user), request
        ).distinct()
    )


def seleccionar_todas_organizaciones(request, user) -> Dict[str, Any]:
    """Todas las organizaciones que matchean, para el boton 'agregar todos'."""

    return _seleccionar_todos(
        ORGANIZACION_ADVANCED_FILTER.filter_queryset(
            _organizaciones_scoped(user), request
        ).distinct()
    )


def etiquetas_de_seleccion(user, comedor_ids: Iterable[int], organizacion_ids) -> Dict:
    """Nombres de los destinatarios ya seleccionados, para pintar los badges."""

    comedor_ids = [int(pk) for pk in comedor_ids or []]
    organizacion_ids = [int(pk) for pk in organizacion_ids or []]
    comedores = (
        _comedores_scoped(user).filter(pk__in=comedor_ids).values_list("pk", "nombre")
        if comedor_ids
        else []
    )
    organizaciones = (
        _organizaciones_scoped(user)
        .filter(pk__in=organizacion_ids)
        .values_list("pk", "nombre")
        if organizacion_ids
        else []
    )
    return {
        "comedores": [
            {"id": pk, "nombre": nombre or f"#{pk}"} for pk, nombre in comedores
        ],
        "organizaciones": [
            {"id": pk, "nombre": nombre or f"#{pk}"} for pk, nombre in organizaciones
        ],
    }


def get_filtros_destinatarios_config() -> Dict[str, Any]:
    """Config de filtros de ambos universos, para el panel de destinatarios."""

    return {
        "comedores": get_comedores_filters_ui_config(),
        "organizaciones": get_organizaciones_filters_ui_config(),
    }


__all__ = [
    "PAGE_SIZE",
    "MAX_SELECCION_MASIVA",
    "buscar_comedores",
    "buscar_organizaciones",
    "seleccionar_todos_comedores",
    "seleccionar_todas_organizaciones",
    "etiquetas_de_seleccion",
    "get_filtros_destinatarios_config",
]
