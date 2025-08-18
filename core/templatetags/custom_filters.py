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
        # Si es None, devolvemos una cadena vacía
        if value is None:
            return ""
        # Si es un objeto relacionado, devolvemos su representación string
        return str(value)
    except (AttributeError, TypeError):
        return ""
