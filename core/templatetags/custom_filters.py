from django import template

register = template.Library()


@register.filter
def has_group(user, group_name):
    if not user or getattr(user, "is_anonymous", True):
        return False

    groups = getattr(user, "_cached_groups", None)
    if groups is None:
        groups = set(user.groups.values_list("name", flat=True))
        setattr(user, "_cached_groups", groups)

    return user.is_superuser or "Admin" in groups or group_name in groups


@register.filter
def endswith(value, suffix):
    try:
        return str(value).lower().endswith(str(suffix).lower())
    except Exception:
        return False
