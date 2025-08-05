from django import template

register = template.Library()


@register.filter
def has_group(user, group_name):
    if not user or not hasattr(user, "groups"):
        return False
    if not hasattr(user, "cached_groups"):
        user.cached_groups = list(user.groups.values_list("name", flat=True))
    return group_name in user.cached_groups


@register.filter
def endswith(value, suffix):
    try:
        return str(value).lower().endswith(str(suffix).lower())
    except Exception:
        return False
