from datetime import date
from decimal import Decimal, InvalidOperation

from django import template
from django.templatetags.static import static
from django.utils.html import format_html

register = template.Library()

_DAYS = (
    "lunes",
    "martes",
    "miercoles",
    "jueves",
    "viernes",
    "sabado",
    "domingo",
)
_MEALS = ("desayuno", "almuerzo", "merienda", "merienda_reforzada", "cena")


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


@register.filter
def default_full_width(value):
    """Garantiza que la tabla sea full width salvo que se especifique lo contrario."""
    if value is None or (isinstance(value, str) and value == ""):
        return True
    return value


@register.filter
def boolean_icon(value):
    if value in [True, 1, "1", "true", "True", "SI", "Sí", "si"]:
        return format_html(
            '<img src="{}" alt="Sí" width="20">',
            static("custom/img/check_ok.svg"),
        )

    if value in [False, 0, "0", "false", "False", "NO", "No", "no"]:
        return format_html(
            '<img src="{}" alt="No" width="20">',
            static("custom/img/check.svg"),
        )

    return "-"


def _is_positive_number(value):
    if value is None:
        return False

    if isinstance(value, str):
        text = value.strip()
        if not text or text == "-":
            return False
        text = text.replace(",", ".")
    else:
        text = value

    try:
        number = Decimal(str(text))
    except (InvalidOperation, ValueError):
        return False

    if number.is_nan() or number.is_infinite():
        return False

    return number > 0


@register.filter
def dias_prestacion_semana(prestacion):
    """
    Cuenta cuántos días a la semana el comedor presta servicio, en base a los
    campos *_<comida>_actual (p.ej. lunes_desayuno_actual) o a los campos
    aprobadas_<comida>_<dia> (p.ej. aprobadas_desayuno_lunes). Si no hay datos,
    devuelve "-".
    """
    if prestacion is None:
        return "-"

    import builtins

    dias_con_servicio = 0
    for day in _DAYS:
        for meal in _MEALS:
            values = (
                builtins.getattr(prestacion, f"{day}_{meal}_actual", None),
                builtins.getattr(prestacion, f"aprobadas_{meal}_{day}", None),
            )
            if any(_is_positive_number(value) for value in values):
                dias_con_servicio += 1
                break

    return dias_con_servicio if dias_con_servicio > 0 else "-"


@register.simple_tag
def replace_query(url, key, value):
    """Return the URL with the query param `key` set to `value`.

    - If the key exists, it is replaced.
    - If the key is missing, it is added.
    - Preserves other query params and fragments.
    Usage:
        {% replace_query request.get_full_path 'admision_id' admision_item.id as adm_url %}
        <a href="{{ adm_url }}">...</a>
    """
    try:
        from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse

        parsed = urlparse(str(url))
        query_items = dict(parse_qsl(parsed.query, keep_blank_values=True))
        query_items[str(key)] = str(value)
        new_query = urlencode(query_items, doseq=True)
        return urlunparse(
            (
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                parsed.params,
                new_query,
                parsed.fragment,
            )
        )
    except Exception:
        # Fallback: naive concatenation ensuring single '?'
        base, _, _ = str(url).partition("?")
        return f"{base}?{key}={value}"
