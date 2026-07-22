from datetime import date
from typing import Any, Optional, Type
import unicodedata

from django.conf import settings
from django.core.cache import cache
from django.db.models import Model
from django.utils import timezone

from comedores.models import PrestacionAlimentariaConformidad, ValorComida
from rendicioncuentasmensual.models import RendicionCuentaMensual

# IDs de programa PNUD en la tabla core_programa (prog 3 = PNUD Prog1, prog 4 = PNUD Prog2).
# Se complementa con la búsqueda por nombre para tolerar entornos donde los IDs difieren.
_PNUD_PROGRAMA_IDS = frozenset((3, 4))


def is_pnud_comedor(comedor) -> bool:
    """Devuelve True si el comedor pertenece a un programa PNUD."""
    programa_nombre = str(
        getattr(getattr(comedor, "programa", None), "nombre", "") or ""
    )
    normalized = " ".join(programa_nombre.lower().split())
    programa_id = getattr(comedor, "programa_id", None)
    return programa_id in _PNUD_PROGRAMA_IDS or "pnud" in normalized


def usa_datos_convenio_pnud(comedor) -> bool:
    """Devuelve True si el comedor usa la carga de convenio PNUD/Abordaje."""
    return is_pnud_comedor(comedor) or (
        "abordaje comunitario" in _get_programa_nombre_normalizado(comedor)
    )


def _normalize_programa(nombre: str) -> str:
    """Remueve acentos y normaliza espacios/mayúsculas en un nombre de programa."""
    sin_acentos = unicodedata.normalize("NFD", nombre)
    sin_acentos = "".join(c for c in sin_acentos if not unicodedata.combining(c))
    return " ".join(sin_acentos.lower().split())


def _get_programa_nombre_normalizado(comedor) -> str:
    nombre = str(getattr(getattr(comedor, "programa", None), "nombre", "") or "")
    return _normalize_programa(nombre)


def is_prestacion_alimentaria_conformidad_program(comedor) -> bool:
    """Programas que gestionan conformidad mensual de prestaciones en mobile."""
    normalized = _get_programa_nombre_normalizado(comedor)
    return normalized == "alimentar comunidad" or "abordaje comunitario" in normalized


def is_abordaje_comunitario_linea_secos_program(comedor) -> bool:
    normalized = _get_programa_nombre_normalizado(comedor)
    return "abordaje comunitario" in normalized and "linea secos" in normalized


def is_abordaje_comunitario_linea_tradicional_program(comedor) -> bool:
    normalized = _get_programa_nombre_normalizado(comedor)
    return "abordaje comunitario" in normalized and "linea tradicional" in normalized


def is_abordaje_comunitario_relevamientos_header_program(comedor) -> bool:
    normalized = _get_programa_nombre_normalizado(comedor)
    return "abordaje comunitario" in normalized and (
        "linea secos" in normalized or "linea tradicional" in normalized
    )


def add_months_period(period: date, months: int) -> date:
    month_index = period.year * 12 + period.month - 1 + months
    return date(month_index // 12, month_index % 12 + 1, 1)


def previous_month_period(today: Optional[date] = None) -> date:
    current = (today or timezone.localdate()).replace(day=1)
    return add_months_period(current, -1)


def get_prestacion_conformidad_convenio_bounds(comedor):
    latest = (
        RendicionCuentaMensual.objects.filter(
            comedor=comedor,
            periodo_inicio__isnull=False,
        )
        .order_by("-periodo_inicio", "-id")
        .first()
    )
    if not latest:
        return None

    queryset = RendicionCuentaMensual.objects.filter(
        comedor=comedor,
        periodo_inicio__isnull=False,
    )
    if latest.convenio:
        queryset = queryset.filter(convenio=latest.convenio)

    start = (
        queryset.order_by("periodo_inicio", "id")
        .values_list("periodo_inicio", flat=True)
        .first()
    )
    if not start:
        return None

    start_period = start.replace(day=1)
    end_period = add_months_period(start_period, 5)
    return start_period, end_period


def get_prestacion_conformidad_periods(comedor, limit: int = 6):
    bounds = get_prestacion_conformidad_convenio_bounds(comedor)
    period = previous_month_period()
    periods = []

    for _ in range(24):
        if bounds:
            start_period, end_period = bounds
            if period < start_period:
                break
            if start_period <= period <= end_period:
                periods.append(period)
        else:
            periods.append(period)

        if len(periods) >= limit:
            break
        period = add_months_period(period, -1)

    return periods


def is_prestacion_conformidad_period_enabled(comedor, period: date) -> bool:
    return period in get_prestacion_conformidad_periods(comedor)


def get_prestacion_conformidad_pending_period(comedor):
    period = previous_month_period()
    certificacion_realizada = (
        PrestacionAlimentariaConformidad.objects.filter(
            comedor=comedor,
            periodo=period,
            certificacion_pdf__isnull=False,
        )
        .exclude(certificacion_pdf="")
        .exists()
    )
    return None if certificacion_realizada else period


def get_object_by_filter(model: Type[Model], **kwargs):
    """Obtener el primer objeto de ``model`` que coincida con ``kwargs``."""
    return model.objects.filter(**kwargs).first()


def get_id_by_nombre(model: Type[Model], nombre: str):
    """Devolver el ``id`` de la instancia cuyo ``nombre`` coincide.

    La comparación no distingue mayúsculas de minúsculas. Retorna cadena vacía
    si no se encuentra coincidencia.
    """
    obj = model.objects.filter(nombre__iexact=nombre).first()
    return obj.id if obj else ""


def normalize_field(valor: Optional[str], chars_to_remove: str) -> Optional[str]:
    """Eliminar caracteres específicos de ``valor`` y normalizar vacíos."""
    if valor:
        for char in chars_to_remove:
            valor = valor.replace(char, "")
    return valor or None


def preload_valores_comida_cache() -> dict[str, Any]:
    """Cargar valores de ``ValorComida`` en cache y devolver el mapeo."""
    valor_map = cache.get("valores_comida_map")
    if not valor_map:
        valores_comida = ValorComida.objects.filter(
            tipo__in=["desayuno", "almuerzo", "merienda", "cena"]
        ).values("tipo", "valor")
        valor_map = {item["tipo"].lower(): item["valor"] for item in valores_comida}
        cache.set("valores_comida_map", valor_map, settings.DEFAULT_CACHE_TIMEOUT)
    return valor_map


def programa_usa_admision_para_nomina(programa: Any) -> bool:
    """Indica si un programa organiza la nómina por admisión.

    El nuevo booleano vive en ``Programas``. Si el objeto todavía no expone el
    campo (fixtures viejos o mocks), se asume ``True`` para no romper el flujo
    histórico.
    """

    if programa is None:
        return True
    return getattr(programa, "usa_admision_para_nomina", True)


def comedor_usa_admision_para_nomina(comedor: Any) -> bool:
    """Indica si el comedor usa admisión para gestionar la nómina."""

    return programa_usa_admision_para_nomina(getattr(comedor, "programa", None))
