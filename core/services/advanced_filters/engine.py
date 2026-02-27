"""Engine principal para filtros avanzados reutilizables."""

from __future__ import annotations

from typing import Any, Callable, Dict, Iterable, Mapping, MutableMapping, Optional

from django.db.models import Q, QuerySet

from .coercion import coerce_value
from .lookups import resolve_lookup
from .payload import extract_raw_filters, load_payload


class AdvancedFilterEngine:
    """Parsea filtros combinables enviados vía querystring y genera ``Q`` objects.

    La expectativa de formato coincide con la implementada originalmente en
    ``ComedorService.get_filtered_comedores``::

        {
          "logic": "AND" | "OR",
          "items": [
            {"field": str, "op": str, "value": Any, "empty_mode": str}
          ]
        }

    Donde la lógica combinada aplica ``OR`` entre filtros del mismo campo y el
    operador global (``AND`` por defecto) entre distintos campos.

    Args:
        field_map: Mapea el identificador expuesto a lookups de Django ORM.
        field_types: Define el tipo lógico de cada campo (por ejemplo ``text``,
            ``choice``, ``number``, ``date`` o ``boolean``). Se usa para validar
            operadores y castear valores.
        allowed_ops: Opcional. Permite personalizar los operadores permitidos por
            tipo. Si no se provee se espera ``{"text": {...}, "number": {...}}``.
        field_casts: Funciones de casteo por campo; útiles cuando se requieren
            conversiones específicas (por ejemplo ``float`` para coordenadas).
        param_name: Nombre del parámetro GET que contiene el JSON de filtros.
    """

    def __init__(
        self,
        *,
        field_map: Mapping[str, str],
        field_types: Mapping[str, str],
        allowed_ops: Optional[Mapping[str, Iterable[str]]] = None,
        field_casts: Optional[Mapping[str, Callable[[Any], Any]]] = None,
        param_name: str = "filters",
    ) -> None:
        self.field_map = dict(field_map)
        self.field_types = dict(field_types)
        self.allowed_ops = {
            key: set(value) for key, value in (allowed_ops or {}).items()
        }
        self.field_casts = dict(field_casts or {})
        self.param_name = param_name

        missing_mappings = set(self.field_types) - set(self.field_map)
        if missing_mappings:
            raise ValueError(
                "AdvancedFilterEngine: field_types contiene claves sin mapeo: "
                + ", ".join(sorted(missing_mappings))
            )

    def filter_queryset(self, queryset: QuerySet, request_or_get: Any) -> QuerySet:
        """Devuelve ``queryset`` filtrado según los datos recibidos.

        Si no se logra construir un filtro válido retorna el queryset original
        sin modificaciones.
        """

        final_q = self.build_q(request_or_get)
        if final_q is None:
            return queryset
        return queryset.filter(final_q)

    def build_q(self, request_or_get: Any) -> Optional[Q]:
        """Construye el ``Q`` resultante a partir de los filtros recibidos."""

        raw_filters = self._extract_raw_filters(request_or_get)
        if not raw_filters:
            return None

        payload = self._load_payload(raw_filters)
        if not payload:
            return None

        items = payload.get("items") or []
        if not isinstance(items, list):
            return None

        groups: Dict[str, list[Q]] = {}
        for item in items:
            if not isinstance(item, MutableMapping):
                continue
            q_item = self._build_q_for_item(item)
            if q_item is None:
                continue
            field_name = item.get("field")
            if not field_name:
                continue
            groups.setdefault(field_name, []).append(q_item)

        if not groups:
            return None

        logic = str(payload.get("logic") or "AND").upper()
        use_or = logic == "OR"

        final_q: Optional[Q] = None
        for q_group in groups.values():
            if not q_group:
                continue
            group_q = q_group[0]
            for extra_q in q_group[1:]:
                group_q = group_q | extra_q

            if final_q is None:
                final_q = group_q
            else:
                final_q = (final_q | group_q) if use_or else (final_q & group_q)

        return final_q

    # --- Internal helpers -------------------------------------------------

    def _extract_raw_filters(self, request_or_get: Any) -> Any:
        """Obtiene el valor del parámetro configurado desde distintas fuentes."""

        return extract_raw_filters(self.param_name, request_or_get)

    def _load_payload(self, raw_filters: Any) -> Optional[dict[str, Any]]:
        """Decodifica el JSON enviado en el parámetro de filtros."""

        return load_payload(raw_filters)

    def _build_q_for_item(self, item: MutableMapping[str, Any]) -> Optional[Q]:
        """Construye el ``Q`` para un filtro individual."""

        field = item.get("field")
        op = item.get("op")
        if not field or field not in self.field_map or not op:
            return None

        mapped_field = self.field_map[field]
        field_type = self.field_types.get(field)
        if not field_type:
            return None

        allowed_ops = self.allowed_ops.get(field_type)
        if allowed_ops is not None and op not in allowed_ops:
            return None

        if op == "empty":
            empty_mode = str(item.get("empty_mode") or "both").lower()
            null_q = Q(**{f"{mapped_field}__isnull": True})
            if field_type == "text":
                blank_q = Q(**{f"{mapped_field}__exact": ""})
                if empty_mode == "null":
                    return null_q
                if empty_mode == "blank":
                    return blank_q
                return null_q | blank_q
            return null_q

        value = item.get("value")
        if value is None or (isinstance(value, str) and value.strip() == ""):
            return None

        ok, casted = self._coerce_value(field, value, field_type)
        if not ok:
            return None

        lookup, negate = resolve_lookup(field_type, op, mapped_field)
        if not lookup:
            return None

        q_object = Q(**{lookup: casted})
        return ~q_object if negate else q_object

    def _coerce_value(
        self, field: str, value: Any, field_type: str
    ) -> tuple[bool, Any]:
        """Intenta castear ``value`` según el tipo del campo."""

        return coerce_value(
            field=field,
            value=value,
            field_type=field_type,
            field_casts=self.field_casts,
        )
