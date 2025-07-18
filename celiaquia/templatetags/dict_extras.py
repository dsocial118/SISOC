# celiaquia/templatetags/dict_extras.py
from django import template

register = template.Library()

@register.filter
def get_item(dict_obj, key):
    """Devuelve dict_obj[key] o cadena vacía si no existe."""
    try:
        return dict_obj.get(key, '')
    except Exception:
        return ''
