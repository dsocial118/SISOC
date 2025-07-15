from django import template

register = template.Library()


@register.filter
def has_group(user, group_name):
    if user.groups.filter(name="Admin").exists() or user.is_superuser:
        return True
    return user.groups.filter(name=group_name).exists()


@register.filter
def endswith(value, suffix):
    try:
        return str(value).lower().endswith(str(suffix).lower())
    except Exception:
        return False
