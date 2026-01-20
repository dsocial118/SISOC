from datetime import date
from decimal import Decimal, InvalidOperation

from django import template

register = template.Library()


@register.filter
def has_group(user, group_name):
    try:
        if not hasattr(user, "cached_groups"):
            user.cached_groups = list(user.groups.values_list("name", flat=True))
        return group_name in user.cached_groups or user.is_superuser
    except Exception:
        return False


@register.filter
def endswith(value, suffix):
    try:
        return str(value).lower().endswith(str(suffix).lower())
    except Exception:
        return False


@register.filter
def is_url(value):
    """
    Detecta si un string es una URL (comienza con /) o un nombre de vista
    Usage: {% if cancel_url|is_url %}{{ cancel_url }}{% else %}{% url cancel_url %}{% endif %}
    """
    try:
        return str(value).startswith("/")
    except AttributeError:
        return False


@register.filter
def getattr(obj, attr_name):
    """
    Obtiene un atributo de un objeto de forma segura, manejando relaciones
    Usage: {{ obj|getattr:"field_name" }}
    """
    import builtins

    try:
        value = builtins.getattr(obj, attr_name, None)
        if value is None:
            return "-"

        # Manejar relaciones M2M haciendo join de sus elementos
        try:
            if hasattr(value, "all") and not isinstance(value, (str, bytes)):
                iterable = value.all()
                return ", ".join(str(v) for v in iterable)
        except Exception:
            # Si falla, caer al string por defecto
            pass

        return str(value)
    except (AttributeError, TypeError):
        return "-"


@register.filter
def edad(fecha_nacimiento):
    """Calcula la edad en años a partir de una fecha de nacimiento"""
    if not fecha_nacimiento:
        return None

    today = date.today()
    return (
        today.year
        - fecha_nacimiento.year
        - ((today.month, today.day) < (fecha_nacimiento.month, fecha_nacimiento.day))
    )


@register.filter
def es_menor_18(fecha_nacimiento):
    """Verifica si una persona es menor de 18 años"""
    if not fecha_nacimiento:
        return False

    edad_actual = edad(fecha_nacimiento)
    return edad_actual is not None and edad_actual < 18


def _normalize_coordinate(value, min_value, max_value):
    if value is None:
        return None

    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        text = text.replace(",", ".")
        if text.count(".") > 1:
            return None
    else:
        text = value

    try:
        decimal_value = Decimal(str(text))
    except (InvalidOperation, ValueError):
        return None

    if decimal_value.is_nan() or decimal_value.is_infinite():
        return None

    min_decimal = Decimal(str(min_value))
    max_decimal = Decimal(str(max_value))
    if decimal_value < min_decimal or decimal_value > max_decimal:
        return None

    return format(decimal_value, "f")


@register.simple_tag
def google_maps_query(latitud, longitud):
    lat_value = _normalize_coordinate(latitud, -90, 90)
    lng_value = _normalize_coordinate(longitud, -180, 180)
    if lat_value is None or lng_value is None:
        return ""
    return f"{lat_value},{lng_value}"
