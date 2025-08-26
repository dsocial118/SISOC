from django import template

register = template.Library()


def _to_float(v, default=0.0):
    """Convierte el valor a float de forma segura."""
    try:
        if v is None:
            return float(default)
        return float(str(v).replace(",", ".").strip())
    except Exception:
        return float(default)


@register.filter
def sum2(a, b):
    """Suma numérica robusta: {{ a|sum2:b }}"""
    return _to_float(a) + _to_float(b)


@register.filter
def pct(part, whole):
    """
    Calcula porcentaje (0–100).
    Uso: {{ parte|pct:total }}
    """
    p = _to_float(part)
    w = _to_float(whole)
    return round((p * 100.0 / w), 2) if w else 0.0


@register.filter
def percent_of(part, whole):
    """Alias de pct (compatibilidad)."""
    return pct(part, whole)


@register.filter
def clamp(value, bounds="0,100"):
    """
    Limita un número a un rango.
    Uso: {{ valor|clamp:"0,100" }}
    """
    try:
        lo_s, hi_s = (bounds or "0,100").split(",")
        lo, hi = float(lo_s), float(hi_s)
        v = _to_float(value)
        if v < lo:
            return lo
        if v > hi:
            return hi
        return v
    except Exception:
        return _to_float(value)


@register.filter
def mul(a, b):
    """Multiplicación: {{ a|mul:b }}"""
    return _to_float(a) * _to_float(b)


@register.filter
def div(a, b):
    """División segura: {{ a|div:b }}"""
    b_val = _to_float(b)
    return (_to_float(a) / b_val) if b_val else 0.0


@register.filter
def sub(a, b):
    """Resta: {{ a|sub:b }}"""
    return _to_float(a) - _to_float(b)
