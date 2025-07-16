from django import template

register = template.Library()


@register.filter
def has_group(user, group_name):
    # Optimización: Cache los grupos del usuario para evitar queries repetidas
    if not hasattr(user, "cached_groups"):
        user.cached_groups = list(user.groups.values_list("name", flat=True))

    if user.is_superuser or "Admin" in user.cached_groups:
        return True
    return group_name in user.cached_groups


@register.filter
def endswith(value, suffix):
    try:
        return str(value).lower().endswith(str(suffix).lower())
    except Exception:
        return False
